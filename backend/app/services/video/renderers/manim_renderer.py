from __future__ import annotations

from app.schemas.video_schema import RenderedVisualResult
from app.schemas.video_schema import VideoScript
from app.services.content_generation_context_service import ContentGenerationContext
from app.services.video.manim_compiler import ManimTemplateCompiler
from app.services.video.manim_plan_generator import ManimPlanGenerator
from app.services.video.manim_runner import ManimCliRunner
from app.services.video.manim_spec_validator import ManimSpecValidator
from app.services.video.workspace import VideoWorkspace, write_json_artifact


class ManimRenderer:
    def __init__(self) -> None:
        self._planner = ManimPlanGenerator()
        self._validator = ManimSpecValidator()
        self._compiler = ManimTemplateCompiler()
        self._runner = ManimCliRunner()

    def plan(
        self,
        *,
        script: VideoScript,
        context: ContentGenerationContext,
        workspace: VideoWorkspace,
        style: str,
        focus_prompt: str | None,
    ):
        spec = self._planner.generate(
            context=context,
            script=script,
            style=style,
            focus_prompt=focus_prompt,
        )
        self._validator.validate(spec)
        write_json_artifact(workspace.spec_path(), spec.model_dump(mode="json"))
        return spec

    def render(
        self,
        *,
        script: VideoScript,
        context: ContentGenerationContext,
        workspace: VideoWorkspace,
        style: str,
        focus_prompt: str | None,
    ) -> RenderedVisualResult:
        spec = self.plan(
            script=script,
            context=context,
            workspace=workspace,
            style=style,
            focus_prompt=focus_prompt,
        )
        compiled = self._compiler.compile(spec=spec, workspace=workspace)
        execution = self._runner.render(
            module_path=compiled.module_path,
            scene_names=compiled.scene_names,
            workspace=workspace,
        )
        artifacts = {
            "render_spec": {
                "path": str(workspace.spec_path()),
                "kind": "json",
                "metadata": {"scene_count": len(spec.scenes)},
            },
            "manim_module": {
                "path": compiled.module_path,
                "kind": "python",
                "metadata": {"scene_names": compiled.scene_names},
            },
            "manim_render_log": {
                "path": str(workspace.render_log_path()),
                "kind": "log",
                "metadata": {},
            },
        }
        for clip in execution.scene_clips:
            artifacts[f"scene_clip_{clip.scene_number:03d}"] = {
                "path": clip.clip_path,
                "kind": "video_clip",
                "metadata": {"scene_name": clip.scene_name},
            }
        return RenderedVisualResult(
            scene_clips=execution.scene_clips,
            preview_path=execution.scene_clips[0].clip_path if execution.scene_clips else None,
            artifacts=artifacts,
        )
