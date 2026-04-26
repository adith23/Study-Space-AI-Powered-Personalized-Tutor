from __future__ import annotations

import subprocess

from pydantic import BaseModel

from app.core.config import settings


class HealthCheckResult(BaseModel):
    ok: bool
    message: str


def check_manim_health() -> HealthCheckResult:
    try:
        result = subprocess.run(
            [settings.MANIM_CLI_BIN, "checkhealth"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        return HealthCheckResult(ok=False, message=f"Manim health check failed: {exc}")

    if result.returncode != 0:
        return HealthCheckResult(
            ok=False,
            message=(result.stderr or result.stdout or "manim checkhealth failed")[-500:],
        )
    return HealthCheckResult(ok=True, message=(result.stdout or "ok")[-500:])


def check_ffmpeg_available() -> HealthCheckResult:
    try:
        result = subprocess.run(
            [settings.FFMPEG_PATH, "-version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception as exc:
        return HealthCheckResult(ok=False, message=f"FFmpeg availability check failed: {exc}")

    if result.returncode != 0:
        return HealthCheckResult(
            ok=False,
            message=(result.stderr or result.stdout or "ffmpeg unavailable")[-500:],
        )
    return HealthCheckResult(ok=True, message="ffmpeg available")
