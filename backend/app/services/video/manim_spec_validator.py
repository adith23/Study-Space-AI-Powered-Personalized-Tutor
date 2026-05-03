from __future__ import annotations

from app.core.config import settings
from app.services.video.manim_spec import (
    AxesPlotBlock,
    ComparisonTableBlock,
    EquationStepBlock,
    FlowDiagramBlock,
    ManimRenderSpec,
)


class ManimSpecValidator:
    def validate(self, spec: ManimRenderSpec) -> None:
        self._validate_scene_count(spec)
        self._validate_scene_numbers(spec)
        self._validate_duration_consistency(spec)
        self._validate_block_count(spec)
        self._validate_text_lengths(spec)
        self._validate_plot_sizes(spec)
        self._validate_grounding(spec)

    def _validate_scene_count(self, spec: ManimRenderSpec) -> None:
        if len(spec.scenes) == 0:
            raise ValueError("Manim render spec must contain at least one scene.")
        if len(spec.scenes) > settings.MANIM_MAX_SCENES:
            raise ValueError("Manim render spec exceeds maximum scene count.")

    def _validate_scene_numbers(self, spec: ManimRenderSpec) -> None:
        seen: set[int] = set()
        previous = 0
        for scene in spec.scenes:
            if scene.scene_number in seen:
                raise ValueError("Manim render spec contains duplicate scene numbers.")
            if scene.scene_number <= previous:
                raise ValueError("Scene numbers must be strictly increasing.")
            seen.add(scene.scene_number)
            previous = scene.scene_number

    def _validate_duration_consistency(self, spec: ManimRenderSpec) -> None:
        for scene in spec.scenes:
            if scene.duration_seconds <= 0:
                raise ValueError("Scene duration must be positive.")

    def _validate_block_count(self, spec: ManimRenderSpec) -> None:
        for scene in spec.scenes:
            if len(scene.visual_blocks) == 0:
                raise ValueError(f"Scene {scene.scene_number} contains no visual blocks.")
            if len(scene.visual_blocks) > settings.MANIM_MAX_BLOCKS_PER_SCENE:
                raise ValueError(
                    f"Scene {scene.scene_number} exceeds maximum visual block count."
                )

    def _validate_text_lengths(self, spec: ManimRenderSpec) -> None:
        max_length = settings.MANIM_MAX_TEXT_LENGTH
        for scene in spec.scenes:
            for text in (scene.scene_name, scene.objective, scene.narration_text):
                if len(text) > max_length:
                    raise ValueError("Scene text exceeds configured text length limit.")
            for block in scene.visual_blocks:
                for key, value in block.model_dump().items():
                    if isinstance(value, str) and len(value) > max_length:
                        raise ValueError(f"Block field '{key}' exceeds text length limit.")
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and len(item) > max_length:
                                raise ValueError(
                                    f"Block field '{key}' contains oversized text."
                                )
                            if isinstance(item, list):
                                for nested in item:
                                    if isinstance(nested, str) and len(nested) > max_length:
                                        raise ValueError(
                                            f"Block field '{key}' contains oversized table cell text."
                                        )

    def _validate_plot_sizes(self, spec: ManimRenderSpec) -> None:
        for scene in spec.scenes:
            for block in scene.visual_blocks:
                if isinstance(block, AxesPlotBlock):
                    if len(block.points) > settings.MANIM_MAX_PLOT_POINTS:
                        raise ValueError("Axes plot exceeds maximum point count.")
                if isinstance(block, ComparisonTableBlock):
                    if len(block.headers) > settings.MANIM_MAX_TABLE_COLUMNS:
                        raise ValueError("Comparison table exceeds maximum column count.")
                    if len(block.rows) > settings.MANIM_MAX_TABLE_ROWS:
                        raise ValueError("Comparison table exceeds maximum row count.")
                if isinstance(block, FlowDiagramBlock):
                    if len(block.nodes) > settings.MANIM_MAX_FLOW_NODES:
                        raise ValueError("Flow diagram exceeds maximum node count.")
                if isinstance(block, EquationStepBlock):
                    if len(block.steps) > settings.MANIM_MAX_EQUATION_STEPS:
                        raise ValueError("Equation block exceeds maximum step count.")

    def _validate_grounding(self, spec: ManimRenderSpec) -> None:
        forbidden_tokens = {"import ", "exec(", "eval(", "__", "subprocess", "open("}
        for scene in spec.scenes:
            for block in scene.visual_blocks:
                flattened = str(block.model_dump()).lower()
                if any(token in flattened for token in forbidden_tokens):
                    raise ValueError("Unsafe or ungrounded content detected in render spec.")
