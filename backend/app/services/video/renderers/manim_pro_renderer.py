"""
Manim Pro renderer strategy.

Uses direct LLM code generation instead of predefined visual block templates
to produce richer, more expressive animated explainer videos.

This renderer exists alongside the existing ``ManimRenderer`` (template-based)
and ``ImageRenderer`` without modifying either.
"""

from __future__ import annotations

from app.schemas.video_schema import RenderedVisualResult, VideoScript
from app.services.content_generation_context_service import ContentGenerationContext
from app.services.video.manim_pro_code_generator import ManimProCodeGenerator
from app.services.video.manim_runner import ManimCliRunner
from app.services.video.workspace import VideoWorkspace


class ManimProRenderer:
    """
    Direct LLM code generation renderer.

    Generates full Manim Python scripts via Gemini and executes them,
    producing richer and more expressive animations than the existing
    template-based ``ManimRenderer``.

    Reuses:
    - ``ManimCliRunner`` for subprocess execution (unchanged)
    - ``VideoWorkspace`` for file management (unchanged)
    - Downstream TTS + assembly stages (unchanged)
    """

    def __init__(self) -> None:
        self._code_generator = ManimProCodeGenerator()
        self._runner = ManimCliRunner()

    def render(
        self,
        *,
        script: VideoScript,
        context: ContentGenerationContext,
        workspace: VideoWorkspace,
        style: str,
        focus_prompt: str | None,
    ) -> RenderedVisualResult:
        """Generate visuals by having the LLM write full Manim code directly."""
        compiled = self._code_generator.generate_and_validate(
            script=script,
            context=context,
            workspace=workspace,
            style=style,
            focus_prompt=focus_prompt,
            runner=self._runner,
        )

        # Build artifacts metadata for the pipeline registry
        artifacts = {
            "manim_pro_module": {
                "path": compiled.module_path,
                "kind": "python",
                "metadata": {
                    "scene_names": compiled.scene_names,
                    "attempts": compiled.attempts,
                },
            },
            "manim_render_log": {
                "path": str(workspace.render_log_path()),
                "kind": "log",
                "metadata": {},
            },
        }
        for clip in compiled.scene_clips:
            artifacts[f"scene_clip_{clip.scene_number:03d}"] = {
                "path": clip.clip_path,
                "kind": "video_clip",
                "metadata": {"scene_name": clip.scene_name},
            }

        return RenderedVisualResult(
            scene_clips=compiled.scene_clips,
            preview_path=(
                compiled.scene_clips[0].clip_path
                if compiled.scene_clips
                else None
            ),
            artifacts=artifacts,
        )
