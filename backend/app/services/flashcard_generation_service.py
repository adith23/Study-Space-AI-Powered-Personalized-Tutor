import json
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.core.config import settings
from app.models.quiz_model import QuizDifficulty, QuizGenerationMode
from app.schemas.flashcard_schema import GeneratedFlashcardPayload
from app.services.content_generation_context_service import ContentGenerationContext


def _build_system_prompt(mode: QuizGenerationMode) -> str:
    mode_instruction = (
        "Create a broad, representative flashcard deck that covers the selected source material."
        if mode == QuizGenerationMode.BROAD_FULL_SOURCE
        else "Create a focused flashcard deck that stays tightly aligned to the requested focus."
    )
    return (
        "You are generating source-grounded study flashcards from supplied material. "
        f"{mode_instruction} "
        "Only use facts directly supported by the supplied context. "
        "Return valid JSON only. Do not use markdown fences. "
        'The JSON must match this shape: {"cards":[{"front_text":"...","back_text":"...","source_snippet":"...","source_metadata":{"section_title":"..."}}]}. '
        "Do not produce duplicate or near-duplicate cards."
    )


def _build_user_prompt(
    *,
    context: ContentGenerationContext,
    difficulty_level: QuizDifficulty,
    number_of_cards: int,
    focus_prompt: str | None,
) -> str:
    focus_line = (
        f"Focus requirement: {focus_prompt.strip()}"
        if focus_prompt
        else "Focus requirement: none. Cover the selected sources broadly."
    )
    return (
        f"Generate exactly {number_of_cards} flashcards.\n"
        f"Difficulty: {difficulty_level.value}.\n"
        f"Generation mode: {context.mode.value}.\n"
        f"{focus_line}\n"
        "Requirements:\n"
        "- Each card must be answerable from the context.\n"
        "- front_text must be concise and suitable for recall.\n"
        "- back_text must provide the grounded answer, definition, or explanation.\n"
        "- easy cards should favor direct recall.\n"
        "- medium cards should emphasize applied understanding or comparison.\n"
        "- hard cards should emphasize synthesis or deeper conceptual distinctions.\n"
        "- Include a short source_snippet copied or paraphrased from the context that supports the card.\n"
        "- Include source_metadata when section information is obvious from the context.\n\n"
        "Context:\n"
        f"{context.context_text}"
    )


def _extract_response_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


def _extract_json_payload(text: str) -> str:
    stripped = text.strip()
    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1)

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("The AI response did not contain a valid JSON object.")
    return stripped[start : end + 1]


def _validate_card_count(
    payload: GeneratedFlashcardPayload, expected_card_count: int
) -> GeneratedFlashcardPayload:
    if len(payload.cards) != expected_card_count:
        raise ValueError(
            f"Expected {expected_card_count} cards but received {len(payload.cards)}."
        )
    return payload


def generate_flashcard_payload(
    *,
    context: ContentGenerationContext,
    difficulty_level: QuizDifficulty,
    number_of_cards: int,
    focus_prompt: str | None,
) -> GeneratedFlashcardPayload:
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHAT_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
    )
    messages = [
        ("system", _build_system_prompt(context.mode)),
        (
            "human",
            _build_user_prompt(
                context=context,
                difficulty_level=difficulty_level,
                number_of_cards=number_of_cards,
                focus_prompt=focus_prompt,
            ),
        ),
    ]

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = llm.invoke(messages)
            payload_text = _extract_json_payload(_extract_response_text(response))
            payload = GeneratedFlashcardPayload.model_validate_json(payload_text)
            return _validate_card_count(payload, number_of_cards)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 0:
                messages.append(
                    (
                        "human",
                        "The previous response was invalid. Return only valid JSON that matches the required schema and card count.",
                    )
                )
                continue
            raise ValueError(
                f"Flashcard generation returned invalid structured output: {exc}"
            ) from exc
        except ChatGoogleGenerativeAIError:
            raise

    if last_error is not None:
        raise last_error
    raise ValueError("Flashcard generation failed without a recoverable response.")
