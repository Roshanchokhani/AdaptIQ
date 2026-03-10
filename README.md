# AdaptIQ — AI-Driven Adaptive Diagnostic Engine

A **1-Dimension Adaptive Testing** prototype that dynamically selects GRE-style questions based on a student's estimated ability level using **Item Response Theory (IRT)**, backed by **FastAPI**, **MongoDB**, and **Claude AI** for personalized study plans.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Adaptive Algorithm](#adaptive-algorithm)
- [API Documentation](#api-documentation)
- [AI Log](#ai-log)

---

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB running locally (`mongodb://localhost:27017`) or a MongoDB Atlas URI
- A Groq API key — free at https://console.groq.com (or Gemini / Anthropic — configurable)

### 1. Clone and set up environment

```bash
git clone <your-repo-url>
cd AdaptIQ

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=adaptiq
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MAX_QUESTIONS_PER_SESSION=20
AI_INSIGHT_TRIGGER=10
```

### 3. Start the API server

```bash
uvicorn app.main:app --reload
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Interactive API documentation |
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000` | *(Bonus)* Browser-based UI for live testing |

### 4. Seed the question bank

```bash
curl -X POST http://localhost:8000/api/v1/questions/seed
```

This loads 22 GRE-style questions spanning difficulties from 0.1 to 1.0 across three topics:
- **Quantitative Reasoning** (algebra, geometry, statistics)
- **Verbal Reasoning** (vocabulary, reading comprehension, rhetoric)
- **Analytical Writing** (logic, argumentation, critical reasoning)

### 5. Run a complete adaptive test session

```bash
# Step 1: Create a session
curl -X POST http://localhost:8000/api/v1/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "student_001"}'
# Returns: {"session_id": "<SESSION_ID>"}

# Step 2: Get the first question
curl http://localhost:8000/api/v1/sessions/<SESSION_ID>/next

# Step 3: Submit an answer
curl -X POST http://localhost:8000/api/v1/sessions/<SESSION_ID>/answer \
  -H "Content-Type: application/json" \
  -d '{"question_id": "<QUESTION_ID>", "answer": "A"}'

# Repeat Steps 2-3. After 10 answers, a personalized study plan is generated.

# Check full session status at any time
curl http://localhost:8000/api/v1/sessions/<SESSION_ID>/status
```

### 6. Run tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
AdaptIQ/
├── app/
│   ├── main.py                      # FastAPI app, lifespan hooks
│   ├── config.py                    # Pydantic settings (env vars)
│   ├── api/v1/
│   │   ├── router.py                # Aggregates all routers
│   │   └── endpoints/
│   │       ├── questions.py         # Question CRUD + seed
│   │       └── sessions.py          # Session lifecycle
│   ├── core/
│   │   ├── database.py              # Motor async MongoDB client
│   │   └── exceptions.py           # Custom HTTP exceptions
│   ├── models/
│   │   ├── question.py              # Question Pydantic models
│   │   └── session.py               # Session + attempt models
│   ├── services/
│   │   ├── question_service.py      # Question DB operations
│   │   ├── session_service.py       # Adaptive test orchestration
│   │   └── insight_service.py       # Claude AI study plan
│   └── utils/
│       ├── irt.py                   # 1PL IRT math (pure functions)
│       └── question_selector.py     # b-matching selector
├── data/
│   └── seed_questions.json          # 22 GRE-style questions
├── tests/
│   ├── test_irt.py                  # IRT unit tests
│   └── test_question_selector.py    # Selector unit tests
├── .env.example
├── requirements.txt
└── README.md
```

---

## Adaptive Algorithm

### Overview

AdaptIQ implements a **1-Parameter Logistic (1PL) Item Response Theory** model, also known as the **Rasch model**. This is a mathematically grounded approach used in real-world adaptive assessments (GRE, GMAT, adaptive standardized tests).

### Core Model

The probability of a student with ability `θ` answering an item with difficulty `b` correctly is:

```
P(correct | θ, b) = 1 / (1 + exp(-(θ - b)))
```

This is a logistic function where:
- **θ (theta)**: Student's current ability estimate (0.1 to 1.0)
- **b**: Item difficulty parameter (0.1 to 1.0)
- When `θ = b`: P = 0.5 (50% chance of correct answer)
- When `θ >> b`: P → 1.0 (easy question for this student)
- When `θ << b`: P → 0.0 (too hard for this student)

### Ability Update Rule

After each response, ability is updated using a gradient ascent step on the Rasch log-likelihood:

```
gradient = response - P(correct | θ, b)
θ_new = θ + learning_rate × gradient
```

Where `response = 1` if correct, `0` if incorrect.

**Why this works:**
- **Correct answer**: `response=1`, `P<1` → positive gradient → θ increases
- **Incorrect answer**: `response=0`, `P>0` → negative gradient → θ decreases
- **Magnitude of change** is largest when `P ≈ 0.5` (well-targeted item), smallest when the question is too easy or too hard

The `learning_rate = 0.3` is calibrated for a 20-question session. θ is clamped to `[0.1, 1.0]` after each update.

### Question Selection: b-Matching

For the 1PL model, **Fisher Information** is:

```
I(θ) = P(correct) × (1 - P(correct))
```

This is maximized when `b = θ` (giving P = 0.5, I = 0.25). Therefore, the optimal next question is the one whose difficulty is **closest to the student's current ability** — this is called the "b-matching" or "maximum information" CAT strategy.

```python
next_question = min(available_questions, key=lambda q: abs(q.difficulty - θ))
```

### Session Flow

```
Student starts at θ = 0.5 (baseline)
    ↓
GET /next-question → select item with b closest to θ
    ↓
Student answers
    ↓
POST /answer → update θ via IRT gradient step
    ↓
If 10 questions answered → generate AI study plan (LLM)
If 20 questions answered → session complete
    ↓
Loop to GET /next-question
```

---

## API Documentation

### Base URL: `http://localhost:8000/api/v1`

---

#### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/sessions/` | Create a new adaptive test session |
| `GET` | `/sessions/{session_id}/next` | Get the next adaptive question |
| `POST` | `/sessions/{session_id}/answer` | Submit an answer, get feedback + updated ability |
| `GET` | `/sessions/{session_id}/status` | Get full session state + study plan |

**POST `/sessions/`**
```json
Request:  { "user_id": "student_001" }
Response: { "session_id": "...", "message": "Session created." }
```

**GET `/sessions/{session_id}/next`**
```json
Response: {
  "id": "question_id",
  "text": "Question text...",
  "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "difficulty": 0.5,
  "topic": "Quantitative Reasoning",
  "tags": ["algebra"]
}
```
Note: `correct_answer` is intentionally omitted from this response.

**POST `/sessions/{session_id}/answer`**
```json
Request:  { "question_id": "...", "answer": "A" }
Response: {
  "is_correct": true,
  "correct_answer": "A",
  "explanation": "Because...",
  "ability_before": 0.50,
  "ability_after": 0.62,
  "questions_answered": 5,
  "session_complete": false,
  "study_plan": null
}
```
When `questions_answered == 10`, `study_plan` contains the AI-generated plan.

---

#### Questions (Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/questions/seed` | Bulk-insert the 22 seed GRE questions |
| `GET` | `/questions/` | List all questions (supports `?topic=` and `?min_difficulty=` filters) |
| `POST` | `/questions/` | Create a single question |
| `GET` | `/questions/{id}` | Get question by ID |
| `DELETE` | `/questions/{id}` | Delete a question |

---

#### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check |

---

## AI Log

### How AI Tools Were Used

**Claude (Anthropic Claude Code)** was used throughout this project as a development accelerator:

1. **Architecture design**: Claude helped design the clean separation between `utils/irt.py` (pure math), `services/session_service.py` (orchestration), and `api/endpoints/` (HTTP layer) — preventing the common mistake of mixing business logic with route handlers.

2. **IRT algorithm validation**: The 1PL gradient update formula (`θ_new = θ + lr × (response - P)`) was validated against the mathematical literature on the Rasch model score equation. Claude confirmed this is the correct gradient of the log-likelihood, not just a heuristic.

3. **MongoDB query optimization**: Claude suggested using `$nin` (not-in) for excluding answered questions and compound indexing on `(difficulty, topic)` for the adaptive query pattern.

4. **Prompt engineering for study plans**: The structured JSON prompt for LLM study plan generation was refined iteratively — the key insight was to explicitly instruct the model to output *only* valid JSON with no markdown wrapper, preventing brittle text parsing.

5. **Edge case identification**: Claude flagged the ability ceiling/floor clamping issue (what happens if θ tries to go below 0.1 after repeated wrong answers), the duplicate-answer submission guard, and the session-already-complete check.

### Note on LLM Provider

The assignment specifies OpenAI or Anthropic API. The codebase is designed to support **all three providers** — Anthropic, OpenAI-compatible (Groq), and Google Gemini — configurable via a single `LLM_PROVIDER` environment variable in `.env`. The AI insight logic (`app/services/insight_service.py`) uses the **Groq API** (serving `llama-3.3-70b-versatile`) as the default due to its free tier availability, but switching to Anthropic Claude requires only changing two lines in `.env`:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
```

The prompt structure, JSON parsing, and fallback handling are identical across all providers.

### Challenges AI Couldn't Solve

1. **Motor async compatibility**: The `AsyncIOMotorClient` type annotations with the FastAPI lifespan context required hands-on debugging. The global client pattern needed careful handling to avoid "client not initialized" errors during startup.

2. **Pydantic v2 + PyObjectId**: The custom `PyObjectId` validator required implementing `__get_pydantic_core_schema__` for Pydantic v2 compatibility — an API change from v1 that Claude initially provided incorrect guidance on.

3. **Session state atomicity**: Designing the `$set` + `$push` combination in a single `update_one` call to avoid race conditions was a judgment call based on application-level reasoning rather than AI suggestion.

---

## Bonus: Browser UI

> **This was not required by the assignment.** It was built as an extra to make the API easier to demo and test interactively.

A single-page interface (`frontend/index.html`) is served at `http://localhost:8000` when the server is running. It lets you run a full adaptive test session in the browser without needing curl or Postman.

**What it shows:**
- Live ability (θ) meter that updates after every answer
- Question card with A/B/C/D options
- Feedback panel with explanation and θ delta after each answer
- AI study plan screen at the 10-question milestone
- Final score summary with accuracy stats

All API calls go to the same FastAPI server — no separate frontend server needed.
