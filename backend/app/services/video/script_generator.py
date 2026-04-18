"""
Stage 1 — Script Generation

Uses Gemini (via LangChain) to analyse source material and produce
a scene-by-scene VideoScript (JSON) suitable for downstream image
and TTS generation.
"""

import json
import re
import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.core.config import settings
from app.schemas.video_schema import VideoScript
from app.services.content_generation_context_service import ContentGenerationContext

logger = logging.getLogger(__name__)

# ── Prompt Engineering ───────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an expert educational video script-writer. "
    "Given study material, produce a structured JSON script for a short "
    "explainer video (approximately 3 minutes). "
    "The script must be ENTIRELY grounded in the supplied context — do NOT "
    "invent facts. "
    "Return valid JSON only. Do not use markdown fences.\n\n"
    "The JSON must match this shape exactly:\n"
    '{"title":"...","scenes":[{"scene_number":1,"narration_text":"...",'
    '"visual_description":"...","duration_seconds":15.0,'
    '"key_concept":"..."}],"total_duration_seconds":180.0}\n\n'
    "Rules:\n"
    "- Create 8-12 scenes that cover the key concepts in a logical flow.\n"
    "- Each scene's narration_text should be 2-4 sentences of clear, "
    "educational narration (as if spoken aloud by a narrator).\n"
    "- Each scene's visual_description should be a detailed prompt for an "
    "AI image generator: describe the illustration style, colours, objects, "
    "and composition. Use 'flat vector educational illustration' style.\n"
    "- duration_seconds per scene should be 10-25 seconds.\n"
    "- total_duration_seconds must equal the sum of all scene durations and "
    "be approximately 180 seconds (3 minutes).\n"
    "- Do not reference prior or next scenes in narration.\n"
    "- Make narration engaging and student-friendly."
)


def _build_user_prompt(
    *,
    context: ContentGenerationContext,
    style: str,
    focus_prompt: str | None,
) -> str:
    style_instruction = {
        "explainer": "Create a clear, step-by-step explainer video.",
        "summary": "Create a concise summary video hitting only the highlights.",
        "deep_dive": "Create an in-depth deep-dive covering nuance and detail.",
    }.get(style, "Create a clear explainer video.")

    focus_line = (
        f"Focus requirement: {focus_prompt.strip()}"
        if focus_prompt
        else "Focus requirement: none — cover the material broadly."
    )

    return (
        f"Video style: {style_instruction}\n"
        f"{focus_line}\n\n"
        f"Source Material:\n{context.context_text}"
    )


# ── Response Parsing ─────────────────────────────────────────────────────────


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
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if fenced:
        return fenced.group(1)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("The AI response did not contain a valid JSON object.")
    return stripped[start : end + 1]


# ── Public API ───────────────────────────────────────────────────────────────


def generate_video_script(
    *,
    context: ContentGenerationContext,
    style: str = "explainer",
    focus_prompt: str | None = None,
) -> VideoScript:
    """Generate a VideoScript from source material using Gemini."""

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHAT_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.4,
    )

    messages = [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            _build_user_prompt(
                context=context,
                style=style,
                focus_prompt=focus_prompt,
            ),
        ),
    ]

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = llm.invoke(messages)
            payload_text = _extract_json_payload(_extract_response_text(response))
            script = VideoScript.model_validate_json(payload_text)

            # Sanity-check scene count
            if not script.scenes:
                raise ValueError("Script contains zero scenes.")

            logger.info(
                "Generated video script: %d scenes, %.0fs total",
                len(script.scenes),
                script.total_duration_seconds,
            )
            return script

        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 0:
                messages.append(
                    (
                        "human",
                        "The previous response was invalid JSON. "
                        "Return only valid JSON matching the required schema.",
                    )
                )
                continue
            raise ValueError(
                f"Script generation returned invalid output: {exc}"
            ) from exc
        except ChatGoogleGenerativeAIError:
            raise

    if last_error is not None:
        raise last_error
    raise ValueError("Script generation failed without a recoverable response.")
