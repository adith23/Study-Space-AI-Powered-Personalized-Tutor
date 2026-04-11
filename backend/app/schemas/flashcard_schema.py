from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.quiz_model import QuizDifficulty, QuizGenerationMode, QuizStatus


class CreateFlashcardDeckRequest(BaseModel):
    file_ids: List[int] = Field(..., min_length=1)
    number_of_cards: int = Field(..., ge=1, le=30)
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


class FlashcardDeckSourceResponse(BaseModel):
    uploaded_file_id: int
    name: Optional[str] = None


class FlashcardResponse(BaseModel):
    id: int
    front_text: str
    back_text: str
    card_order: int


class FlashcardDeckResponse(BaseModel):
    id: int
    title: str
    difficulty_level: QuizDifficulty
    number_of_cards: int
    focus_prompt: Optional[str] = None
    generation_mode: QuizGenerationMode
    status: QuizStatus
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FlashcardDeckDetailResponse(FlashcardDeckResponse):
    sources: List[FlashcardDeckSourceResponse]
    cards: List[FlashcardResponse] = []


class GeneratedFlashcard(BaseModel):
    front_text: str
    back_text: str
    source_snippet: Optional[str] = None
    source_metadata: Optional[dict] = None


class GeneratedFlashcardPayload(BaseModel):
    cards: List[GeneratedFlashcard]
