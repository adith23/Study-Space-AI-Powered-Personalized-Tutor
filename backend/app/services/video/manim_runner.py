from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from pydantic import BaseModel

from app.core.config import settings
from app.schemas.video_schema import RenderedSceneClip
from app.services.video.workspace import VideoWorkspace

logger = logging.getLogger(__name__)


class RenderExecutionResult(BaseModel):
    scene_clips: list[RenderedSceneClip]
    stdout: str = ""
    stderr: str = ""


class ManimCliRunner:
    def render(
        self,
        *,
        module_path: str,
        scene_names: list[str],
        workspace: VideoWorkspace,
    ) -> RenderExecutionResult:
        clips: list[RenderedSceneClip] = []
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []

        for index, scene_name in enumerate(scene_names, start=1):
            output_name = f"scene_{index:03d}"
            command = self._build_command(
                module_path=module_path,
                scene_name=scene_name,
                output_name=output_name,
                workspace=workspace,
            )
            result = self._run_subprocess(command, cwd=str(workspace.root))
            stdout_parts.append(result.stdout or "")
            stderr_parts.append(result.stderr or "")
            if result.returncode != 0:
                env_error = self._detect_manim_environment_error(result.stderr or "")
                raise RuntimeError(
                    env_error
                    or f"Manim render failed for {scene_name}: {(result.stderr or 'unknown error')[-500:]}"
                )
            clip_path = self._find_rendered_clip(workspace, output_name)
            clips.append(
                RenderedSceneClip(
                    scene_number=index,
                    scene_name=scene_name,
                    clip_path=str(clip_path),
                )
            )

        workspace.render_log_path().write_text(
            "\n".join(stdout_parts + stderr_parts), encoding="utf-8"
        )
        return RenderExecutionResult(
            scene_clips=clips,
            stdout="\n".join(stdout_parts),
            stderr="\n".join(stderr_parts),
        )

    def _build_command(
        self,
        *,
        module_path: str,
        scene_name: str,
        output_name: str,
        workspace: VideoWorkspace,
    ) -> list[str]:
        command = [
            settings.MANIM_CLI_BIN,
            "render",
            module_path,
            scene_name,
            f"-q{settings.MANIM_RENDER_QUALITY}",
            "--format",
            "mp4",
            "--media_dir",
            str(workspace.manim_media_dir()),
            "--output_file",
            output_name,
        ]
        if settings.MANIM_DISABLE_CACHING:
            command.append("--disable_caching")
        return command

    def _run_subprocess(
        self,
        command: list[str],
        *,
        cwd: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        logger.info("Running Manim command: %s", " ".join(command))
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=settings.MANIM_RENDER_TIMEOUT_SECONDS,
        )

    def _find_rendered_clip(self, workspace: VideoWorkspace, output_name: str) -> Path:
        matches = list(workspace.manim_media_dir().rglob(f"{output_name}.mp4"))
        if not matches:
            raise RuntimeError(f"Expected rendered clip {output_name}.mp4 not found.")
        return matches[0]

    def _detect_manim_environment_error(self, stderr: str) -> str | None:
        lowered = stderr.lower()
        if "latex" in lowered and "not found" in lowered:
            return "Manim render failed because LaTeX is unavailable for a TeX-backed scene."
        if "ffmpeg" in lowered and "not found" in lowered:
            return "Manim render failed because FFmpeg is unavailable in the runtime environment."
        if "no module named manim" in lowered:
            return "Manim runtime is not installed in the worker environment."
        return None
