"""
Stage 4 - Video Assembly

Uses FFmpeg to create or align scene clips, concatenate them into the final MP4,
and extract a thumbnail.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from app.core.config import settings
from app.schemas.video_schema import AssemblyResult
from app.schemas.video_schema import AudioClipResult
from app.schemas.video_schema import RenderedSceneClip
from app.services.video.workspace import VideoWorkspace

logger = logging.getLogger(__name__)


def _run_ffmpeg(
    args: list[str],
    description: str,
    *,
    cwd: str | None = None,
    log_path: str | Path | None = None,
) -> None:
    cmd = [settings.FFMPEG_PATH] + args
    logger.info("FFmpeg [%s]: %s", description, " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
        cwd=cwd,
    )
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(f"$ {' '.join(cmd)}\n")
            handle.write(result.stdout or "")
            handle.write(result.stderr or "")
            handle.write("\n")
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed ({description}): {result.stderr[-500:] if result.stderr else 'unknown error'}"
        )


def _probe_duration(media_path: str) -> float:
    result = subprocess.run(
        [
            settings.FFPROBE_PATH,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            media_path,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def create_scene_clips_from_images(
    *,
    image_paths: list[str],
    audio_results: list[AudioClipResult],
    workspace: VideoWorkspace,
) -> list[RenderedSceneClip]:
    clips: list[RenderedSceneClip] = []
    for image_path, audio in zip(image_paths, sorted(audio_results, key=lambda item: item.scene_number)):
        clip_path = workspace.scene_clip_dir() / f"scene_{audio.scene_number:03d}.mp4"
        zoom_filter = (
            f"zoompan=z='min(zoom+0.0005,1.1)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={int(audio.duration_seconds * 25)}:s=1280x720:fps=25"
        )
        _run_ffmpeg(
            [
                "-y",
                "-loop",
                "1",
                "-i",
                image_path,
                "-vf",
                zoom_filter,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-tune",
                "stillimage",
                "-pix_fmt",
                "yuv420p",
                "-an",
                "-t",
                str(audio.duration_seconds),
                str(clip_path),
            ],
            description=f"image clip scene_{audio.scene_number:03d}",
            log_path=workspace.ffmpeg_log_path(),
        )
        clips.append(
            RenderedSceneClip(
                scene_number=audio.scene_number,
                scene_name=f"Scene{audio.scene_number:02d}",
                clip_path=str(clip_path),
                duration_seconds=audio.duration_seconds,
            )
        )
    return clips


def _freeze_last_frame(
    *,
    clip_path: str,
    output_path: str,
    target_duration: float,
    workspace: VideoWorkspace,
) -> str:
    _run_ffmpeg(
        [
            "-y",
            "-i",
            clip_path,
            "-vf",
            "tpad=stop_mode=clone:stop_duration={:.3f}".format(max(target_duration, 0.0)),
            "-c:v",
            "libx264",
            "-an",
            output_path,
        ],
        description="freeze pad clip",
        log_path=workspace.ffmpeg_log_path(),
    )
    return output_path


def _trim_visual_clip(
    *,
    clip_path: str,
    output_path: str,
    target_duration: float,
    workspace: VideoWorkspace,
) -> str:
    _run_ffmpeg(
        [
            "-y",
            "-i",
            clip_path,
            "-t",
            str(target_duration),
            "-c:v",
            "libx264",
            "-an",
            output_path,
        ],
        description="trim clip",
        log_path=workspace.ffmpeg_log_path(),
    )
    return output_path


def _align_clip_to_audio(
    *,
    clip: RenderedSceneClip,
    audio: AudioClipResult,
    workspace: VideoWorkspace,
) -> str:
    clip_duration = clip.duration_seconds or _probe_duration(clip.clip_path)
    delta = audio.duration_seconds - clip_duration
    output_path = workspace.aligned_clip_dir() / f"aligned_{clip.scene_number:03d}.mp4"
    tolerance = settings.VIDEO_ALIGNMENT_TOLERANCE_SECONDS

    if abs(delta) <= tolerance:
        shutil.copyfile(clip.clip_path, output_path)
        return str(output_path)
    if delta > 0:
        return _freeze_last_frame(
            clip_path=clip.clip_path,
            output_path=str(output_path),
            target_duration=delta,
            workspace=workspace,
        )
    return _trim_visual_clip(
        clip_path=clip.clip_path,
        output_path=str(output_path),
        target_duration=audio.duration_seconds,
        workspace=workspace,
    )


def _attach_audio_to_clip(
    *,
    clip_path: str,
    audio: AudioClipResult,
    output_path: str,
    workspace: VideoWorkspace,
) -> str:
    _run_ffmpeg(
        [
            "-y",
            "-i",
            clip_path,
            "-i",
            audio.audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            output_path,
        ],
        description="attach audio to clip",
        log_path=workspace.ffmpeg_log_path(),
    )
    return output_path


def _concatenate_aligned_clips(
    *,
    clip_paths: list[str],
    output_path: str,
    workspace: VideoWorkspace,
) -> None:
    concat_file = workspace.root / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as handle:
        for clip in clip_paths:
            rel_clip = os.path.relpath(clip, workspace.root).replace("\\", "/")
            handle.write(f"file '{rel_clip}'\n")

    _run_ffmpeg(
        [
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            "concat_list.txt",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            Path(output_path).name,
        ],
        description="concatenate aligned clips",
        cwd=str(Path(output_path).parent),
        log_path=workspace.ffmpeg_log_path(),
    )
    try:
        concat_file.unlink()
    except OSError:
        pass


def _generate_thumbnail(video_path: str, thumbnail_path: str, workspace: VideoWorkspace) -> None:
    _run_ffmpeg(
        ["-y", "-i", video_path, "-vframes", "1", "-q:v", "2", thumbnail_path],
        description="generate thumbnail",
        log_path=workspace.ffmpeg_log_path(),
    )


class VisualAssemblyService:
    def assemble_scene_clips(
        self,
        *,
        scene_clips: list[RenderedSceneClip],
        audio_results: list[AudioClipResult],
        workspace: VideoWorkspace,
    ) -> AssemblyResult:
        ordered_clips = sorted(scene_clips, key=lambda item: item.scene_number)
        ordered_audio = sorted(audio_results, key=lambda item: item.scene_number)
        if len(ordered_clips) != len(ordered_audio):
            raise ValueError("Rendered clip count does not match audio clip count.")

        muxed_paths: list[str] = []
        total_duration = 0.0
        for clip, audio in zip(ordered_clips, ordered_audio):
            if clip.scene_number != audio.scene_number:
                raise ValueError("Scene clips and audio clips are not aligned by scene number.")
            aligned_clip = _align_clip_to_audio(clip=clip, audio=audio, workspace=workspace)
            muxed_path = workspace.assembled_dir() / f"muxed_{clip.scene_number:03d}.mp4"
            _attach_audio_to_clip(
                clip_path=aligned_clip,
                audio=audio,
                output_path=str(muxed_path),
                workspace=workspace,
            )
            muxed_paths.append(str(muxed_path))
            total_duration += audio.duration_seconds

        output_path = workspace.output_video_path()
        _concatenate_aligned_clips(
            clip_paths=muxed_paths,
            output_path=str(output_path),
            workspace=workspace,
        )
        _generate_thumbnail(str(output_path), str(workspace.thumbnail_path()), workspace)
        return AssemblyResult(
            video_path=str(output_path),
            thumbnail_path=str(workspace.thumbnail_path()),
            duration_seconds=total_duration,
        )
