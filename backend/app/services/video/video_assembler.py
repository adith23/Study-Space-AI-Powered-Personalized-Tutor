"""
Stage 4 — Video Assembly

Uses FFmpeg (via subprocess) to combine scene images and audio clips
into a final narrated MP4 video with Ken Burns animation and crossfade
transitions.
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def _run_ffmpeg(args: list[str], description: str) -> None:
    """Run an FFmpeg command and raise on failure."""
    cmd = [settings.FFMPEG_PATH] + args
    logger.info("FFmpeg [%s]: %s", description, " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        logger.error("FFmpeg stderr: %s", result.stderr[-2000:] if result.stderr else "")
        raise RuntimeError(
            f"FFmpeg failed ({description}): {result.stderr[-500:] if result.stderr else 'unknown error'}"
        )


def _create_scene_clip(
    *,
    image_path: str,
    audio_path: str,
    output_path: str,
    duration: float,
) -> None:
    """
    Create a single scene clip: a still image with Ken Burns (zoom) effect
    matched to the audio duration.
    """
    # Ken Burns: slow zoom from 100% to 110% over the duration
    zoom_filter = (
        f"zoompan=z='min(zoom+0.0005,1.1)':x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':d={int(duration * 25)}:s=1280x720:fps=25"
    )

    _run_ffmpeg(
        [
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-filter_complex", zoom_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-t", str(duration),
            output_path,
        ],
        description=f"scene clip {os.path.basename(output_path)}",
    )


def _concatenate_clips(
    clip_paths: list[str],
    output_path: str,
) -> None:
    """Concatenate scene clips into a single video using FFmpeg concat demuxer."""
    # Write the concat file list
    concat_dir = os.path.dirname(output_path)
    concat_file = os.path.join(concat_dir, "concat_list.txt")

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in clip_paths:
            # FFmpeg concat demuxer requires forward slashes or escaped backslashes
            safe_path = clip.replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    _run_ffmpeg(
        [
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path,
        ],
        description="concatenate scenes",
    )

    # Cleanup temp concat file
    try:
        os.remove(concat_file)
    except OSError:
        pass


def _generate_thumbnail(video_path: str, thumbnail_path: str) -> None:
    """Extract the first frame of the video as a JPEG thumbnail."""
    _run_ffmpeg(
        [
            "-y",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            thumbnail_path,
        ],
        description="generate thumbnail",
    )


def assemble_video(
    *,
    image_paths: list[str],
    audio_results: list[tuple[str, float]],
    video_dir: str,
) -> tuple[str, str, float]:
    """
    Assemble all scene images and audio clips into a final MP4 video.

    Args:
        image_paths: Ordered list of scene image file paths.
        audio_results: Ordered list of (audio_path, duration_seconds) tuples.
        video_dir: Base directory for this video's assets.

    Returns:
        Tuple of (video_path, thumbnail_path, total_duration_seconds).
    """
    clips_dir = os.path.join(video_dir, "clips")
    Path(clips_dir).mkdir(parents=True, exist_ok=True)

    output_path = os.path.join(video_dir, "output.mp4")
    thumbnail_path = os.path.join(video_dir, "thumbnail.jpg")

    # Step 1: Create individual scene clips
    clip_paths: list[str] = []
    total_duration = 0.0

    for i, (image_path, (audio_path, duration)) in enumerate(
        zip(image_paths, audio_results)
    ):
        clip_path = os.path.join(clips_dir, f"clip_{i:03d}.mp4")
        _create_scene_clip(
            image_path=image_path,
            audio_path=audio_path,
            output_path=clip_path,
            duration=duration,
        )
        clip_paths.append(clip_path)
        total_duration += duration

    logger.info("Created %d scene clips (%.0fs total)", len(clip_paths), total_duration)

    # Step 2: Concatenate all clips
    _concatenate_clips(clip_paths, output_path)
    logger.info("Assembled final video → %s", output_path)

    # Step 3: Generate thumbnail
    _generate_thumbnail(output_path, thumbnail_path)
    logger.info("Generated thumbnail → %s", thumbnail_path)

    # Cleanup intermediate clips
    for clip in clip_paths:
        try:
            os.remove(clip)
        except OSError:
            pass
    try:
        os.rmdir(clips_dir)
    except OSError:
        pass

    return output_path, thumbnail_path, total_duration
