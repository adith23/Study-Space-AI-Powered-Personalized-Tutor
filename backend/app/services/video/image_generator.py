"""
Stage 2 — Image Generation

Uses the google-genai unified SDK with the Gemini 2.5 Flash Image model
to generate educational illustrations for each video scene.
"""

import logging
import os
import time
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.video_schema import VideoScene

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # seconds

# Shared style prefix to ensure visual consistency across all scenes
STYLE_PREFIX = (
    "Flat vector educational illustration, clean modern design, "
    "vibrant colours on a soft gradient background, no text overlays, "
    "16:9 aspect ratio, suitable for an educational explainer video. "
)


def _get_genai_client() -> genai.Client:
    """Create a google-genai client using the existing Gemini API key."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_scene_image(
    *,
    scene: VideoScene,
    output_dir: str,
) -> str:
    """
    Generate an illustration for a single scene.

    Returns the absolute path to the saved image file.
    """
    client = _get_genai_client()
    prompt = f"{STYLE_PREFIX}{scene.visual_description}"
    output_path = os.path.join(output_dir, f"scene_{scene.scene_number:03d}.png")

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=settings.VIDEO_IMAGE_MODEL,
                contents=[prompt],
            )

            # Extract image bytes from the response parts
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    Path(output_dir).mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(part.inline_data.data)
                    logger.info(
                        "Generated image for scene %d → %s",
                        scene.scene_number,
                        output_path,
                    )
                    return output_path

            raise ValueError(
                f"No image data in response for scene {scene.scene_number}"
            )

        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "Image generation failed for scene %d (attempt %d/%d). "
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
                    "Image generation failed for scene %d after %d attempts: %s",
                    scene.scene_number,
                    MAX_RETRIES,
                    exc,
                )

    raise RuntimeError(
        f"Image generation failed for scene {scene.scene_number} "
        f"after {MAX_RETRIES} attempts."
    ) from last_error


def generate_all_scene_images(
    *,
    scenes: list[VideoScene],
    video_dir: str,
) -> list[str]:
    """
    Generate illustrations for all scenes in sequence.

    Returns a list of absolute paths to the saved image files,
    ordered by scene number.
    """
    output_dir = os.path.join(video_dir, "scenes")
    image_paths: list[str] = []

    for scene in scenes:
        path = generate_scene_image(scene=scene, output_dir=output_dir)
        image_paths.append(path)

    logger.info("Generated %d scene images in %s", len(image_paths), output_dir)
    return image_paths
