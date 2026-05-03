from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.core.config import settings
from app.schemas.video_schema import VideoScript
from app.services.content_generation_context_service import ContentGenerationContext
from app.services.video.manim_spec import ManimRenderSpec

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an expert technical animation planner for Manim Community Edition.
Given grounded educational source context and a narration script, produce a valid JSON render plan.
Do not output Python. Do not output markdown fences. Output JSON only.

The plan must match this shape:
{
  "title": "...",
  "theme": {"palette_name": "...", "background_color": "#0b1020", "accent_color": "#60a5fa", "text_color": "#f8fafc"},
  "pacing": {"transition_style": "fade", "reveal_speed": "medium"},
  "scenes": [
    {
      "scene_number": 1,
      "scene_name": "Foundations",
      "objective": "...",
      "narration_text": "...",
      "duration_seconds": 15.0,
      "visual_blocks": [...]
    }
  ]
}

Allowed block types only:
- title_card
- bullet_build
- highlight_definition
- equation_step
- axes_plot
- flow_diagram
- comparison_table

Rules:
- Keep the plan grounded in the supplied material.
- Prefer simple clear technical visuals.
- Do not invent data, equations, labels, or formulas not present or directly implied by the source context.
- Use at least one visual block per scene.
- Use only fields required by each block type.
- Use concise scene names suitable as Python class names after sanitization.
"""


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


class ManimPlanGenerator:
    def __init__(self) -> None:
        self._llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
        )

    def _build_prompt(
        self,
        *,
        context: ContentGenerationContext,
        script: VideoScript,
        style: str,
        focus_prompt: str | None,
    ) -> str:
        return (
            f"Video style: {style}\n"
            f"Focus prompt: {focus_prompt or 'broad coverage'}\n\n"
            f"Narration script JSON:\n{script.model_dump_json(indent=2)}\n\n"
            f"Grounding source context:\n{context.context_text}"
        )

    def _repair_prompt(self, raw_error: str) -> str:
        return (
            "The previous response was invalid against the schema. "
            "Return valid JSON only and fix this issue:\n"
            f"{raw_error}"
        )

    def generate(
        self,
        *,
        context: ContentGenerationContext,
        script: VideoScript,
        style: str,
        focus_prompt: str | None,
    ) -> ManimRenderSpec:
        messages: list[tuple[str, str]] = [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                self._build_prompt(
                    context=context,
                    script=script,
                    style=style,
                    focus_prompt=focus_prompt,
                ),
            ),
        ]

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = self._llm.invoke(messages)
                payload_text = _extract_json_payload(_extract_response_text(response))
                return ManimRenderSpec.model_validate_json(payload_text)
            except (ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == 0:
                    messages.append(("human", self._repair_prompt(str(exc))))
                    continue
                raise ValueError(f"Invalid Manim render spec: {exc}") from exc
            except ChatGoogleGenerativeAIError:
                raise

        if last_error:
            raise last_error
        raise ValueError("Failed to generate Manim render spec.")
