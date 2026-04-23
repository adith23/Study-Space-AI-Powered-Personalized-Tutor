"""
Stage 2 — Image Generation

Uses the google-genai unified SDK with the Gemini 2.5 Flash Image model
to generate educational illustrations for each video scene.
Falls back to styled Pillow placeholders when the AI model is unavailable.
"""

import logging
import math
import os
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.video_schema import VideoScene

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # seconds

# Tracks whether the last generate_scene_image call used AI or placeholder
_last_scene_used_ai = True

# Shared style prefix to ensure visual consistency across all scenes
STYLE_PREFIX = (
    "Flat vector educational illustration, clean modern design, "
    "vibrant colours on a soft gradient background, no text overlays, "
    "16:9 aspect ratio, suitable for an educational explainer video. "
)

# Color palette for placeholder backgrounds (harmonious gradient pairs)
_PALETTE = [
    ((45, 45, 80), (80, 60, 130)),  # Deep indigo
    ((20, 60, 80), (40, 120, 140)),  # Teal ocean
    ((80, 30, 60), (150, 50, 90)),  # Berry
    ((30, 60, 40), (60, 130, 80)),  # Forest
    ((80, 50, 20), (160, 100, 40)),  # Amber
    ((50, 30, 80), (100, 60, 160)),  # Purple
    ((20, 50, 80), (50, 100, 180)),  # Ocean blue
    ((70, 30, 30), (150, 60, 50)),  # Crimson
    ((30, 70, 70), (60, 140, 130)),  # Jade
    ((60, 60, 30), (130, 130, 50)),  # Olive gold
    ((40, 40, 60), (90, 80, 140)),  # Lavender
    ((60, 40, 40), (140, 80, 70)),  # Terracotta
]


def _get_genai_client() -> genai.Client:
    """Create a google-genai client using the existing Gemini API key."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _generate_placeholder(
    *,
    scene: "VideoScene",
    output_path: str,
    output_dir: str,
) -> str:
    """
    Generate a styled placeholder image using Pillow.
    Creates a gradient background with scene number and description text.
    """
    width, height = 1280, 720
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Pick colors from palette based on scene number
    c1, c2 = _PALETTE[(scene.scene_number - 1) % len(_PALETTE)]

    # Draw vertical gradient
    for y in range(height):
        ratio = y / height
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Draw decorative circles
    for i in range(6):
        cx = 200 + i * 200
        cy = 150 + (i % 3) * 180
        radius = 40 + (i % 4) * 20
        overlay_color = (255, 255, 255, 15)
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=None,
            outline=(255, 255, 255, 40),
            width=2,
        )

    # Use default font (no external font files needed)
    try:
        font_large = ImageFont.truetype("arial.ttf", 72)
        font_medium = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Scene number badge
    badge_text = f"SCENE {scene.scene_number}"
    draw.rounded_rectangle(
        [40, 30, 320, 100],
        radius=12,
        fill=(0, 0, 0, 80),
    )
    draw.text((60, 40), badge_text, fill=(255, 255, 255), font=font_large)

    # Visual description text (wrapped)
    desc = scene.visual_description or "Educational content"
    wrapped = textwrap.wrap(desc, width=50)
    y_offset = 300
    for line in wrapped[:6]:  # Max 6 lines
        draw.text(
            (80, y_offset),
            line,
            fill=(255, 255, 255, 220),
            font=font_medium,
        )
        y_offset += 38

    # Footer
    draw.text(
        (80, height - 50),
        "⬡ Study Space — AI Placeholder",
        fill=(255, 255, 255, 120),
        font=font_small,
    )

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    logger.info(
        "Generated placeholder image for scene %d → %s",
        scene.scene_number,
        output_path,
    )
    return output_path


def generate_scene_image(
    *,
    scene: VideoScene,
    output_dir: str,
) -> str:
    """
    Generate an illustration for a single scene.

    Returns the absolute path to the saved image file.
    """
    global _last_scene_used_ai
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
                    _last_scene_used_ai = True
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

    # Fallback to placeholder when AI image generation is unavailable
    _last_scene_used_ai = False
    logger.warning(
        "Falling back to placeholder image for scene %d",
        scene.scene_number,
    )
    return _generate_placeholder(
        scene=scene,
        output_path=output_path,
        output_dir=output_dir,
    )


def generate_all_scene_images(
    *,
    scenes: list[VideoScene],
    video_dir: str,
) -> list[str]:
    """
    Generate illustrations for all scenes in sequence.

    Tries AI generation for the first scene. If it fails and falls back
    to a placeholder, all subsequent scenes use placeholders directly
    (avoids wasting time retrying a model with zero quota).

    Returns a list of absolute paths to the saved image files,
    ordered by scene number.
    """
    output_dir = os.path.join(video_dir, "scenes")
    image_paths: list[str] = []
    use_placeholders = False

    for scene in scenes:
        output_path = os.path.join(
            output_dir, f"scene_{scene.scene_number:03d}.png"
        )

        if use_placeholders:
            # Skip AI entirely — already know it's unavailable
            path = _generate_placeholder(
                scene=scene,
                output_path=output_path,
                output_dir=output_dir,
            )
        else:
            path = generate_scene_image(scene=scene, output_dir=output_dir)

            # Check if we fell back to a placeholder (AI failed)
            # If so, switch to placeholder-only mode for remaining scenes
            if not _last_scene_used_ai:
                use_placeholders = True
                logger.info(
                    "AI image generation unavailable — using placeholders "
                    "for all remaining scenes."
                )

        image_paths.append(path)

    logger.info("Generated %d scene images in %s", len(image_paths), output_dir)
    return image_paths
