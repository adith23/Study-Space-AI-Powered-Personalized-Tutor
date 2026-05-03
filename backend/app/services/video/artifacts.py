from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VideoArtifactRegistry:
    artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)

    def record(
        self,
        name: str,
        path: str,
        kind: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.artifacts[name] = {
            "path": path,
            "kind": kind,
            "metadata": metadata or {},
        }

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return dict(self.artifacts)


def build_artifacts_snapshot(registry: VideoArtifactRegistry) -> dict[str, dict[str, Any]]:
    return registry.snapshot()
