from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class ThemeSpec(BaseModel):
    palette_name: str = "study_space"
    background_color: str = "#0b1020"
    accent_color: str = "#60a5fa"
    text_color: str = "#f8fafc"


class PacingSpec(BaseModel):
    transition_style: str = "fade"
    reveal_speed: Literal["slow", "medium", "fast"] = "medium"


class BaseVisualBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    block_type: str


class TitleCardBlock(BaseVisualBlock):
    block_type: Literal["title_card"]
    title: str
    subtitle: str | None = None


class BulletBuildBlock(BaseVisualBlock):
    block_type: Literal["bullet_build"]
    heading: str
    bullets: list[str]


class HighlightDefinitionBlock(BaseVisualBlock):
    block_type: Literal["highlight_definition"]
    term: str
    definition: str


class EquationStepBlock(BaseVisualBlock):
    block_type: Literal["equation_step"]
    title: str | None = None
    steps: list[str]


class PlotPoint(BaseModel):
    x: float
    y: float


class AxesPlotBlock(BaseVisualBlock):
    block_type: Literal["axes_plot"]
    title: str | None = None
    x_label: str
    y_label: str
    points: list[PlotPoint]
    x_range: tuple[float, float] | None = None
    y_range: tuple[float, float] | None = None


class FlowDiagramBlock(BaseVisualBlock):
    block_type: Literal["flow_diagram"]
    title: str | None = None
    nodes: list[str]


class ComparisonTableBlock(BaseVisualBlock):
    block_type: Literal["comparison_table"]
    title: str | None = None
    headers: list[str]
    rows: list[list[str]]


VisualBlockUnion = Annotated[
    TitleCardBlock
    | BulletBuildBlock
    | HighlightDefinitionBlock
    | EquationStepBlock
    | AxesPlotBlock
    | FlowDiagramBlock
    | ComparisonTableBlock,
    Field(discriminator="block_type"),
]


class ManimSceneSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_number: int
    scene_name: str
    objective: str
    narration_text: str
    duration_seconds: float
    visual_blocks: list[VisualBlockUnion]


class ManimRenderSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    theme: ThemeSpec = Field(default_factory=ThemeSpec)
    pacing: PacingSpec = Field(default_factory=PacingSpec)
    scenes: list[ManimSceneSpec]
