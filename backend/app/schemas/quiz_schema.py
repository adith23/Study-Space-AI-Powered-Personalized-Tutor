from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.quiz_model import QuizDifficulty, QuizGenerationMode, QuizStatus


class CreateQuizRequest(BaseModel):
    file_ids: List[int] = Field(..., min_length=1)
    number_of_questions: int = Field(..., ge=1, le=20)
    difficulty_level: QuizDifficulty
    focus_prompt: Optional[str] = None
    title: Optional[str] = None

    @field_validator("focus_prompt", "title")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class QuizSourceResponse(BaseModel):
    uploaded_file_id: int
    name: Optional[str] = None


class QuizQuestionResponse(BaseModel):
    id: int
    question_text: str
    options: List[str]
    question_order: int


class QuizResponse(BaseModel):
    id: int
    title: str
    difficulty_level: QuizDifficulty
    number_of_questions: int
    focus_prompt: Optional[str] = None
    generation_mode: QuizGenerationMode
    status: QuizStatus
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuizDetailResponse(QuizResponse):
    sources: List[QuizSourceResponse]
    questions: List[QuizQuestionResponse] = []


class SubmitQuizAnswerRequest(BaseModel):
    question_id: int
    selected_option: str = Field(..., min_length=1, max_length=1)

    @field_validator("selected_option")
    @classmethod
    def normalize_selected_option(cls, value: str) -> str:
        option = value.strip().upper()
        if option not in {"A", "B", "C", "D"}:
            raise ValueError("selected_option must be one of A, B, C, or D")
        return option


class SubmitQuizAttemptRequest(BaseModel):
    answers: List[SubmitQuizAnswerRequest] = Field(..., min_length=1)


class QuizAttemptAnswerResultResponse(BaseModel):
    question_id: int
    question_text: str
    options: List[str]
    selected_option: str
    correct_option: str
    is_correct: bool


class QuizAttemptResultResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    score: int
    percentage: float
    total_questions: int
    answers: List[QuizAttemptAnswerResultResponse]


class GeneratedQuizQuestion(BaseModel):
    question_text: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_option: str = Field(..., min_length=1, max_length=1)
    source_snippet: Optional[str] = None
    source_metadata: Optional[dict] = None

    @field_validator("correct_option")
    @classmethod
    def validate_correct_option(cls, value: str) -> str:
        option = value.strip().upper()
        if option not in {"A", "B", "C", "D"}:
            raise ValueError("correct_option must be one of A, B, C, or D")
        return option


class GeneratedQuizPayload(BaseModel):
    questions: List[GeneratedQuizQuestion]
