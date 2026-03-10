from fastapi import HTTPException, status


class SessionNotFoundError(HTTPException):
    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )


class QuestionNotFoundError(HTTPException):
    def __init__(self, question_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found.",
        )


class SessionCompleteError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="This session is already complete.",
        )


class DuplicateAnswerError(HTTPException):
    def __init__(self, question_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question '{question_id}' has already been answered in this session.",
        )


class NoQuestionsAvailableError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No more questions available for this session.",
        )
