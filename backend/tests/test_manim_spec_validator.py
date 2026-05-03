from app.services.video.manim_spec import (
    BulletBuildBlock,
    ManimRenderSpec,
    ManimSceneSpec,
)
from app.services.video.manim_spec_validator import ManimSpecValidator


def test_valid_manim_spec_passes_validation():
    spec = ManimRenderSpec(
        title="Binary Search",
        scenes=[
            ManimSceneSpec(
                scene_number=1,
                scene_name="Overview",
                objective="Explain the search space",
                narration_text="Binary search splits the sorted range in half.",
                duration_seconds=12.0,
                visual_blocks=[
                    BulletBuildBlock(
                        block_type="bullet_build",
                        heading="Binary Search",
                        bullets=["Sorted data", "Midpoint check", "Halve the range"],
                    )
                ],
            )
        ],
    )

    ManimSpecValidator().validate(spec)


def test_duplicate_scene_numbers_are_rejected():
    spec = ManimRenderSpec(
        title="Bad Spec",
        scenes=[
            ManimSceneSpec(
                scene_number=1,
                scene_name="One",
                objective="A",
                narration_text="A",
                duration_seconds=10.0,
                visual_blocks=[
                    BulletBuildBlock(
                        block_type="bullet_build",
                        heading="A",
                        bullets=["one"],
                    )
                ],
            ),
            ManimSceneSpec(
                scene_number=1,
                scene_name="Two",
                objective="B",
                narration_text="B",
                duration_seconds=10.0,
                visual_blocks=[
                    BulletBuildBlock(
                        block_type="bullet_build",
                        heading="B",
                        bullets=["two"],
                    )
                ],
            ),
        ],
    )

    try:
        ManimSpecValidator().validate(spec)
    except ValueError as exc:
        assert "duplicate scene numbers" in str(exc).lower()
    else:
        raise AssertionError("Expected duplicate scene numbers to be rejected.")
