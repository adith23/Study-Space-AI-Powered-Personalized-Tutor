from pathlib import Path

from app.services.video.manim_compiler import ManimTemplateCompiler
from app.services.video.manim_spec import (
    BulletBuildBlock,
    ManimRenderSpec,
    ManimSceneSpec,
)
from app.services.video.workspace import VideoWorkspace


def test_compiler_emits_expected_scene_class(tmp_path: Path):
    spec = ManimRenderSpec(
        title="Stacks",
        scenes=[
            ManimSceneSpec(
                scene_number=1,
                scene_name="LIFO Basics",
                objective="Show last-in first-out behavior",
                narration_text="A stack removes the last item that was added.",
                duration_seconds=11.0,
                visual_blocks=[
                    BulletBuildBlock(
                        block_type="bullet_build",
                        heading="Stack",
                        bullets=["Push adds", "Pop removes", "Top inspects"],
                    )
                ],
            )
        ],
    )
    workspace = VideoWorkspace(video_id=99, root=tmp_path / "99")
    workspace.ensure_dirs()

    compiled = ManimTemplateCompiler().compile(spec=spec, workspace=workspace)

    assert "class Scene01LifoBasics(Scene):" in compiled.source_code
    assert "bullet_group = VGroup" in compiled.source_code
    assert Path(compiled.module_path).exists()
