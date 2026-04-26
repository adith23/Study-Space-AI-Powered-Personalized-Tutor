from __future__ import annotations

from app.schemas.video_schema import RenderedVisualResult
from app.schemas.video_schema import VideoScript
from app.services.video.image_generator import generate_all_scene_images
from app.services.video.workspace import VideoWorkspace


class ImageRenderer:
    def render(
        self,
        *,
        script: VideoScript,
        workspace: VideoWorkspace,
        **_: object,
    ) -> RenderedVisualResult:
        image_paths = generate_all_scene_images(
            scenes=script.scenes,
            video_dir=str(workspace.root),
        )
        artifacts = {
            f"scene_image_{index:03d}": {
                "path": path,
                "kind": "image",
                "metadata": {"scene_number": index},
            }
            for index, path in enumerate(image_paths, start=1)
        }
        return RenderedVisualResult(
            image_paths=image_paths,
            artifacts=artifacts,
        )
