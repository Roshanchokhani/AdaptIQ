"""
AI Insights Service — generates a personalized 3-step study plan.

Supports three LLM providers, configured via LLM_PROVIDER in .env:
  - groq      → uses groq Python SDK  (llama-3.3-70b-versatile)
  - gemini    → uses google-generativeai SDK (gemini-1.5-flash)
  - anthropic → uses anthropic SDK (claude-opus-4-5)
"""

import json
from collections import defaultdict
from app.config import settings
from app.models.session import StudyPlan, QuestionAttempt


def _aggregate_by_topic(attempts: list[QuestionAttempt]) -> dict:
    topic_stats: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
    for attempt in attempts:
        topic_stats[attempt.topic]["total"] += 1
        if attempt.is_correct:
            topic_stats[attempt.topic]["correct"] += 1
    return dict(topic_stats)


def _build_prompt(ability: float, topic_stats: dict, total_answered: int) -> str:
    topic_lines = []
    for topic, stats in topic_stats.items():
        pct = int((stats["correct"] / stats["total"]) * 100) if stats["total"] > 0 else 0
        topic_lines.append(f"  - {topic}: {stats['correct']}/{stats['total']} correct ({pct}%)")

    topic_breakdown = "\n".join(topic_lines) if topic_lines else "  - No topic data available"
    ability_pct = int(ability * 100)

    return f"""You are an expert GRE tutor and learning coach. A student has just completed {total_answered} adaptive GRE-style questions.

Student Performance Summary:
- Estimated ability level: {ability:.2f}/1.00 ({ability_pct}th percentile equivalent)
- Questions answered: {total_answered}
- Performance by topic:
{topic_breakdown}

Based on this performance data, create a personalized 3-step study plan targeting their specific weaknesses.

Respond with ONLY valid JSON in exactly this format, with no markdown or extra text:
{{
  "assessment": "A single sentence summarizing the student's current level and primary challenge.",
  "steps": [
    {{
      "step": 1,
      "focus": "The specific topic or skill to address",
      "action": "A concrete, actionable study task (e.g., 'Complete 20 practice problems on quadratic equations')",
      "resource_type": "practice_problems"
    }},
    {{
      "step": 2,
      "focus": "...",
      "action": "...",
      "resource_type": "reading"
    }},
    {{
      "step": 3,
      "focus": "...",
      "action": "...",
      "resource_type": "video"
    }}
  ]
}}

resource_type must be one of: practice_problems, reading, video, flashcards, mock_test"""


def _fallback_plan(reason: str) -> StudyPlan:
    return StudyPlan(
        assessment=f"AI insights unavailable: {reason}",
        steps=[
            {"step": 1, "focus": "General Review", "action": "Review all incorrect answers.", "resource_type": "practice_problems"},
            {"step": 2, "focus": "Weak Topics", "action": "Focus additional practice on low-scoring topics.", "resource_type": "reading"},
            {"step": 3, "focus": "Test Strategy", "action": "Practice timed test sections.", "resource_type": "mock_test"},
        ],
    )


def _parse_response(raw_text: str) -> StudyPlan:
    text = raw_text.strip()
    # Strip markdown code fences if the model wraps JSON in ```json ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        data = json.loads(text)
        return StudyPlan(assessment=data["assessment"], steps=data["steps"])
    except (json.JSONDecodeError, KeyError):
        return StudyPlan(
            assessment=text[:500],
            steps=[{"step": 1, "focus": "See assessment", "action": text, "resource_type": "reading"}],
        )


def _call_groq(prompt: str) -> str:
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.3,
    )
    return response.choices[0].message.content


def _call_gemini(prompt: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


def _call_anthropic(prompt: str) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def generate_study_plan(attempts: list[QuestionAttempt], current_ability: float) -> StudyPlan:
    """
    Generate a personalized 3-step study plan using the configured LLM provider.

    Provider is selected via LLM_PROVIDER in .env:
      groq      → GROQ_API_KEY required
      gemini    → GEMINI_API_KEY required
      anthropic → ANTHROPIC_API_KEY required
    """
    provider = settings.LLM_PROVIDER.lower()

    api_key_map = {
        "groq": settings.GROQ_API_KEY,
        "gemini": settings.GEMINI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
    }

    if provider not in api_key_map:
        return _fallback_plan(f"Unknown LLM_PROVIDER '{provider}'. Use groq, gemini, or anthropic.")

    if not api_key_map[provider]:
        return _fallback_plan(f"{provider.upper()}_API_KEY not configured in .env")

    topic_stats = _aggregate_by_topic(attempts)
    prompt = _build_prompt(current_ability, topic_stats, len(attempts))

    try:
        if provider == "groq":
            raw = _call_groq(prompt)
        elif provider == "gemini":
            raw = _call_gemini(prompt)
        else:
            raw = _call_anthropic(prompt)

        return _parse_response(raw)

    except Exception as e:
        return _fallback_plan(f"{provider} API error: {str(e)[:200]}")
