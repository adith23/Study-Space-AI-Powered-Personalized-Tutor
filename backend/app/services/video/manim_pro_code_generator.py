"""
Manim Pro — Direct LLM Code Generation

Generates complete, executable Manim Community Edition Python scripts
via Gemini, with a self-healing retry loop that feeds runtime errors
back to the LLM for automatic repair.

This module is part of the ``manim_pro`` renderer pipeline and does NOT
modify or depend on the existing template-based ``manim`` renderer code.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from app.core.config import settings
from app.schemas.video_schema import RenderedSceneClip, VideoScript
from app.services.content_generation_context_service import \
    ContentGenerationContext
from app.services.video.manim_runner import ManimCliRunner
from app.services.video.workspace import VideoWorkspace, write_text_artifact

logger = logging.getLogger(__name__)


# ── Prompt Engineering ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert Manim Community Edition programmer who creates beautiful, \
professional educational animations.

Given an educational narration script and source material, produce a COMPLETE, \
EXECUTABLE Python file using the Manim library (Manim Community Edition).

CRITICAL RULES:
- Output ONLY valid Python code. No markdown fences, no explanations, no \
comments outside the code.
- The file MUST start with `from manim import *`
- Define exactly one Scene subclass per narration scene, named Scene01, \
Scene02, Scene03, etc.
- Each Scene class MUST have a `construct(self)` method.
- Do NOT use any external files, images, SVGs, sounds, or network calls.
- Do NOT use deprecated Manim APIs.
- Do NOT use Tex or MathTex unless the content is explicitly a LaTeX \
mathematical formula. Use Text() for all regular text.
- Do NOT use OpenGLRenderer or any renderer-specific APIs.

VISUAL DESIGN REQUIREMENTS:
- Set `self.camera.background_color = "#0b1020"` in every scene.
- Use a consistent color palette:
  - ACCENT: "#60a5fa" (blue) for highlights, titles, key terms
  - TEXT: "#f8fafc" (white) for body text
  - SECONDARY: "#34d399" (green) for secondary highlights
  - WARN: "#fbbf24" (amber) for warnings or emphasis
  - SUBTLE: "#94a3b8" (gray) for subtle elements
- Title font size: 40-48, Body text: 24-32, Labels: 20-24
- Always ensure text and objects fit within the frame — use .scale() if needed.
- Use .to_edge(), .to_corner(), .move_to(ORIGIN), .next_to() for precise layout.

ANIMATION QUALITY GUIDELINES:
- Use VGroup to organize related objects and animate them together.
- Use LaggedStart for sequential reveals of bullet points, list items, or \
diagram nodes.
- Use smooth transitions between concepts: FadeOut old content before \
introducing new content.
- Add visual emphasis with: SurroundingRectangle, Underline, Indicate, \
Circumscribe, Flash.
- For processes and flows: use Arrow, CurvedArrow, and organized node layouts.
- For comparisons: use side-by-side layouts with clear dividers.
- For data visualization: use BarChart, Axes with plotted points/functions, \
NumberLine.
- For hierarchies: use tree-like structures with connecting lines.
- Use self.wait(0.5) to self.wait(1.5) between logical sections for pacing.
- End each scene with `self.play(FadeOut(*self.mobjects))` for clean transitions.
- Use run_time parameter to control animation speed (0.3-0.8 for quick, \
1.0-2.0 for emphasis).

STRUCTURE:
- Start Scene01 with a title card introducing the topic.
- Use remaining scenes to explain concepts with rich visuals.
- Build complexity gradually — simple elements first, then add detail.
- Each scene should be self-contained (clear all objects at the end).
"""


REPAIR_PROMPT_TEMPLATE = """\
The previous code FAILED with this runtime error:

```
{error}
```

Here is the code that failed:

```python
{original_code}
```

Fix ALL issues and return the COMPLETE corrected Python file. \
Output ONLY the fixed Python code, nothing else.

Common fixes to apply:
- Replace any deprecated API calls with current Manim Community Edition \
equivalents.
- Fix all indentation and syntax errors.
- Ensure all variables are defined before use.
- Use Text() instead of Tex()/MathTex() if LaTeX is not required or causing \
errors.
- Scale down objects that overflow the frame using .scale().
- Fix any import issues — only `from manim import *` is needed.
- Ensure all string literals are properly closed.
- If a class or method doesn't exist in Manim CE, find the correct alternative.
- Make sure there are no circular references or infinite loops in animations.
"""


# ── Data Structures ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ManimProCompileResult:
    """Result of a successful Manim Pro code generation and rendering."""

    module_path: str
    scene_names: list[str]
    scene_clips: list[RenderedSceneClip]
    source_code: str
    attempts: int


# ── Response Parsing ─────────────────────────────────────────────────────────


def _extract_response_text(response: Any) -> str:
    """Extract text content from a LangChain LLM response."""
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


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences if the LLM wrapped output in them."""
    stripped = text.strip()
    fenced = re.search(r"```(?:python)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return stripped


def _extract_scene_names(code: str) -> list[str]:
    """Parse Scene class names from generated Python code.

    Looks for classes named ``Scene01``, ``Scene02``, etc. that inherit
    from ``Scene``.  Falls back to any class inheriting from common Manim
    scene base classes.
    """
    matches = re.findall(
        r"^class\s+(Scene\d+\w*)\s*\(\s*Scene\s*\)\s*:",
        code,
        re.MULTILINE,
    )
    if not matches:
        matches = re.findall(
            r"^class\s+(\w+)\s*\(\s*(?:Scene|MovingCameraScene|ThreeDScene)\s*\)\s*:",
            code,
            re.MULTILINE,
        )
    return matches


# ── Prompt Builders ──────────────────────────────────────────────────────────


def _build_user_prompt(
    *,
    script: VideoScript,
    context: ContentGenerationContext,
    style: str,
    focus_prompt: str | None,
) -> str:
    """Build the user-facing prompt with narration script and grounding context."""
    style_instruction = {
        "explainer": (
            "Create a clear, step-by-step explainer with detailed visuals "
            "for each concept."
        ),
        "summary": "Create a concise summary with impactful key-point visuals.",
        "deep_dive": (
            "Create an in-depth deep-dive with rich, detailed, and layered "
            "animations."
        ),
    }.get(style, "Create a clear explainer video.")

    focus_line = (
        f"Focus requirement: {focus_prompt.strip()}"
        if focus_prompt
        else "Focus requirement: none — cover the material broadly."
    )

    scenes_description = "\n".join(
        f'Scene {s.scene_number}: "{s.narration_text}" '
        f"(duration: ~{s.duration_seconds}s, key concept: {s.key_concept})"
        for s in script.scenes
    )

    return (
        f"Video style: {style_instruction}\n"
        f"{focus_line}\n\n"
        f"Video title: {script.title}\n"
        f"Total duration: ~{script.total_duration_seconds}s\n\n"
        f"Scene-by-scene narration script:\n{scenes_description}\n\n"
        f"Grounding source context:\n{context.context_text}"
    )


# ── Code Generator ───────────────────────────────────────────────────────────


class ManimProCodeGenerator:
    """
    Generates complete Manim Python scripts via Gemini LLM.

    Includes a self-healing retry loop: if the generated code fails
    at runtime, the error traceback is fed back to the LLM for
    automatic repair (up to ``MANIM_PRO_MAX_RETRIES`` attempts).
    """

    def __init__(self) -> None:
        self._llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
        )
        self._max_retries = settings.MANIM_PRO_MAX_RETRIES

    def generate_and_validate(
        self,
        *,
        script: VideoScript,
        context: ContentGenerationContext,
        workspace: VideoWorkspace,
        style: str,
        focus_prompt: str | None,
        runner: ManimCliRunner,
    ) -> ManimProCompileResult:
        """
        Generate Manim code via LLM and validate it by running ``manim render``.

        On failure the runtime error is appended to the conversation and the
        LLM is asked to fix the code.  This continues for up to
        ``self._max_retries`` total attempts.
        """
        messages: list[tuple[str, str]] = [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                _build_user_prompt(
                    script=script,
                    context=context,
                    style=style,
                    focus_prompt=focus_prompt,
                ),
            ),
        ]

        last_error: Exception | None = None
        last_code: str = ""

        for attempt in range(1, self._max_retries + 1):
            logger.info(
                "Manim Pro code generation attempt %d/%d for workspace %s",
                attempt,
                self._max_retries,
                workspace.root,
            )

            try:
                # ── Generate code from LLM ───────────────────────────
                response = self._llm.invoke(messages)
                raw_text = _extract_response_text(response)
                code = _strip_markdown_fences(raw_text)
                last_code = code

                # ── Validate: must contain Scene subclasses ──────────
                scene_names = _extract_scene_names(code)
                if not scene_names:
                    raise ValueError(
                        "Generated code does not contain any Scene subclasses. "
                        "Expected classes like Scene01(Scene), Scene02(Scene), etc."
                    )

                # ── Write code to workspace ──────────────────────────
                module_path = workspace.manim_module_path()
                write_text_artifact(module_path, code)
                logger.info(
                    "Written Manim Pro module with %d scenes: %s",
                    len(scene_names),
                    scene_names,
                )

                # ── Execute manim render to validate ─────────────────
                execution = runner.render(
                    module_path=str(module_path),
                    scene_names=scene_names,
                    workspace=workspace,
                )

                logger.info(
                    "Manim Pro render succeeded on attempt %d with %d clips",
                    attempt,
                    len(execution.scene_clips),
                )

                return ManimProCompileResult(
                    module_path=str(module_path),
                    scene_names=scene_names,
                    scene_clips=execution.scene_clips,
                    source_code=code,
                    attempts=attempt,
                )

            except ChatGoogleGenerativeAIError:
                # API-level errors (quota, auth, etc.) — do not retry
                raise

            except Exception as exc:
                last_error = exc
                error_message = str(exc)
                logger.warning(
                    "Manim Pro attempt %d/%d failed: %s",
                    attempt,
                    self._max_retries,
                    error_message[:300],
                )

                if attempt < self._max_retries:
                    # Feed error back to LLM for self-healing
                    repair_prompt = REPAIR_PROMPT_TEMPLATE.format(
                        error=error_message[:2000],
                        original_code=last_code[:8000],
                    )
                    messages.append(("human", repair_prompt))
                    continue

        raise RuntimeError(
            f"Manim Pro code generation failed after {self._max_retries} "
            f"attempts. Last error: {last_error}"
        ) from last_error
