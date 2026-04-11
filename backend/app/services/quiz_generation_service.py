import json
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.core.config import settings
from app.models.quiz_model import QuizDifficulty, QuizGenerationMode
from app.schemas.quiz_schema import GeneratedQuizPayload
from app.services.quiz_context_service import QuizGenerationContext


def _build_system_prompt(mode: QuizGenerationMode) -> str:
    mode_instruction = (
        "Create a broad, representative quiz that covers the selected source material."
        if mode == QuizGenerationMode.BROAD_FULL_SOURCE
        else "Create a focused quiz that stays tightly aligned to the requested focus."
    )
    return (
        "You are generating a source-grounded multiple-choice quiz from supplied study material. "
        f"{mode_instruction} "
        "Only use facts that are directly supported by the supplied context. "
        "Return valid JSON only. Do not use markdown fences. "
        'The JSON must match this shape: {"questions":[{"question_text":"...","options":["...","...","...","..."],'
        '"correct_option":"A","source_snippet":"...","source_metadata":{"section_title":"..."}}]}. '
        "Each question must have exactly 4 options. "
        "correct_option must be one of A, B, C, or D. "
        "Do not produce duplicate or near-duplicate questions. "
        "Avoid trick questions and unsupported inferences."
    )


def _build_user_prompt(
    *,
    context: QuizGenerationContext,
    difficulty_level: QuizDifficulty,
    number_of_questions: int,
    focus_prompt: str | None,
) -> str:
    focus_line = (
        f"Focus requirement: {focus_prompt.strip()}"
        if focus_prompt
        else "Focus requirement: none. Cover the selected sources broadly."
    )
    return (
        f"Generate exactly {number_of_questions} questions.\n"
        f"Difficulty: {difficulty_level.value}.\n"
        f"Generation mode: {context.mode.value}.\n"
        f"{focus_line}\n"
        "Requirements:\n"
        "- Each question must be answerable from the context.\n"
        "- Provide one clearly correct answer and three plausible distractors.\n"
        "- Keep wording concise and student-facing.\n"
        "- Include a short source_snippet copied or paraphrased from the context that supports the answer.\n"
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


def _validate_question_count(
    payload: GeneratedQuizPayload, expected_question_count: int
) -> GeneratedQuizPayload:
    if len(payload.questions) != expected_question_count:
        raise ValueError(
            f"Expected {expected_question_count} questions but received {len(payload.questions)}."
        )
    return payload


def generate_quiz_payload(
    *,
    context: QuizGenerationContext,
    difficulty_level: QuizDifficulty,
    number_of_questions: int,
    focus_prompt: str | None,
) -> GeneratedQuizPayload:
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
                number_of_questions=number_of_questions,
                focus_prompt=focus_prompt,
            ),
        ),
    ]

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = llm.invoke(messages)
            payload_text = _extract_json_payload(_extract_response_text(response))
            payload = GeneratedQuizPayload.model_validate_json(payload_text)
            return _validate_question_count(payload, number_of_questions)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 0:
                messages.append(
                    (
                        "human",
                        "The previous response was invalid. Return only valid JSON that matches the required schema and question count.",
                    )
                )
                continue
            raise ValueError(f"Quiz generation returned invalid structured output: {exc}") from exc
        except ChatGoogleGenerativeAIError:
            raise

    if last_error is not None:
        raise last_error
    raise ValueError("Quiz generation failed without a recoverable response.")
