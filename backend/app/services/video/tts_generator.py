"""
Stage 3 - TTS Audio Generation

Uses Gemini native TTS via the google-genai unified SDK to generate
narration audio for each video scene.
"""

from __future__ import annotations

import logging
import os
import time
import wave
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.video_schema import AudioClipResult
from app.schemas.video_schema import VideoScene
from app.services.video.workspace import VideoWorkspace

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5


def _get_genai_client() -> genai.Client:
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _save_wav(audio_bytes: bytes, output_path: str) -> float:
    sample_rate = 24000
    sample_width = 2
    channels = 1

    Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)

    num_frames = len(audio_bytes) // (sample_width * channels)
    return num_frames / sample_rate


def generate_scene_audio(
    *,
    scene: VideoScene,
    output_dir: str,
) -> AudioClipResult:
    client = _get_genai_client()
    output_path = os.path.join(output_dir, f"scene_{scene.scene_number:03d}.wav")

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=settings.VIDEO_TTS_MODEL,
                contents=scene.narration_text,
                config=types.GenerateContentConfig(
                    response_modalities=["audio"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=settings.VIDEO_TTS_VOICE,
                            )
                        )
                    ),
                ),
            )

            audio_data = response.candidates[0].content.parts[0].inline_data.data
            if not audio_data:
                raise ValueError(f"Empty audio data for scene {scene.scene_number}")

            duration = _save_wav(audio_data, output_path)
            logger.info(
                "Generated audio for scene %d: %.1fs -> %s",
                scene.scene_number,
                duration,
                output_path,
            )
            return AudioClipResult(
                scene_number=scene.scene_number,
                audio_path=output_path,
                duration_seconds=duration,
            )

        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "TTS generation failed for scene %d (attempt %d/%d). Retrying in %ds: %s",
                    scene.scene_number,
                    attempt,
                    MAX_RETRIES,
                    delay,
                    exc,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "TTS generation failed for scene %d after %d attempts: %s",
                    scene.scene_number,
                    MAX_RETRIES,
                    exc,
                )

    raise RuntimeError(
        f"TTS generation failed for scene {scene.scene_number} after {MAX_RETRIES} attempts."
    ) from last_error


def generate_all_scene_audio(
    *,
    scenes: list[VideoScene],
    workspace: VideoWorkspace,
) -> list[AudioClipResult]:
    results: list[AudioClipResult] = []

    for scene in scenes:
        result = generate_scene_audio(scene=scene, output_dir=str(workspace.audio_dir()))
        results.append(result)

    total = sum(item.duration_seconds for item in results)
    logger.info(
        "Generated %d audio clips (%.0fs total) in %s",
        len(results),
        total,
        workspace.audio_dir(),
    )
    return results
