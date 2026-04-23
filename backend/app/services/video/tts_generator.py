"""
Stage 3 — TTS Audio Generation

Uses Gemini native TTS (gemini-3.1-flash-tts-preview) via the google-genai
unified SDK to generate narration audio for each video scene.
"""

import logging
import os
import struct
import time
import wave
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.video_schema import VideoScene

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5  # seconds


def _get_genai_client() -> genai.Client:
    """Create a google-genai client using the existing Gemini API key."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _save_wav(audio_bytes: bytes, output_path: str) -> float:
    """
    Save raw PCM audio bytes as a WAV file and return the duration in seconds.

    The Gemini TTS API returns raw linear PCM data (16-bit, 24kHz, mono).
    We wrap it in a proper WAV header.
    """
    sample_rate = 24000
    sample_width = 2  # 16-bit = 2 bytes
    channels = 1

    Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)

    num_frames = len(audio_bytes) // (sample_width * channels)
    duration = num_frames / sample_rate
    return duration


def generate_scene_audio(
    *,
    scene: VideoScene,
    output_dir: str,
) -> tuple[str, float]:
    """
    Generate narration audio for a single scene.

    Returns a tuple of (absolute_path_to_wav, duration_seconds).
    """
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

            # Extract audio bytes from the response
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            if not audio_data:
                raise ValueError(f"Empty audio data for scene {scene.scene_number}")

            duration = _save_wav(audio_data, output_path)
            logger.info(
                "Generated audio for scene %d: %.1fs → %s",
                scene.scene_number,
                duration,
                output_path,
            )
            return output_path, duration

        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "TTS generation failed for scene %d (attempt %d/%d). "
                    "Retrying in %ds: %s",
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
        f"TTS generation failed for scene {scene.scene_number} "
        f"after {MAX_RETRIES} attempts."
    ) from last_error


def generate_all_scene_audio(
    *,
    scenes: list[VideoScene],
    video_dir: str,
) -> list[tuple[str, float]]:
    """
    Generate narration audio for all scenes in sequence.

    Returns a list of (audio_path, duration_seconds) tuples,
    ordered by scene number.
    """
    output_dir = os.path.join(video_dir, "audio")
    results: list[tuple[str, float]] = []

    for scene in scenes:
        path, duration = generate_scene_audio(scene=scene, output_dir=output_dir)
        results.append((path, duration))

    total = sum(d for _, d in results)
    logger.info(
        "Generated %d audio clips (%.0fs total) in %s",
        len(results),
        total,
        output_dir,
    )
    return results
