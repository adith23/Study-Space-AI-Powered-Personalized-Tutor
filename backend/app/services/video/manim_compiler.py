from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

from app.services.video.manim_spec import ManimRenderSpec
from app.services.video.manim_templates import (
    AxesPlotTemplate,
    BulletBuildTemplate,
    ComparisonTableTemplate,
    CompileContext,
    EquationStepTemplate,
    FlowDiagramTemplate,
    HighlightDefinitionTemplate,
    TitleCardTemplate,
)
from app.services.video.workspace import VideoWorkspace, write_text_artifact


@dataclass(frozen=True)
class CompiledManimModule:
    module_path: str
    scene_names: list[str]
    source_code: str


class ManimTemplateCompiler:
    def __init__(self) -> None:
        self._dispatch = {
            "title_card": TitleCardTemplate(),
            "bullet_build": BulletBuildTemplate(),
            "highlight_definition": HighlightDefinitionTemplate(),
            "equation_step": EquationStepTemplate(),
            "axes_plot": AxesPlotTemplate(),
            "flow_diagram": FlowDiagramTemplate(),
            "comparison_table": ComparisonTableTemplate(),
        }

    def compile(
        self,
        *,
        spec: ManimRenderSpec,
        workspace: VideoWorkspace,
    ) -> CompiledManimModule:
        scene_names: list[str] = []
        buffer: list[str] = [self._emit_imports(), self._emit_theme_constants(spec)]

        for scene in spec.scenes:
            class_name = self._normalize_scene_name(scene.scene_name, scene.scene_number)
            scene_names.append(class_name)
            buffer.append(self._emit_scene_class(class_name, scene))

        source_code = "\n".join(buffer)
        write_text_artifact(workspace.manim_module_path(), source_code)
        return CompiledManimModule(
            module_path=str(workspace.manim_module_path()),
            scene_names=scene_names,
            source_code=source_code,
        )

    def _emit_imports(self) -> str:
        return "\n".join(
            [
                "from manim import *",
                "",
            ]
        )

    def _emit_theme_constants(self, spec: ManimRenderSpec) -> str:
        theme = spec.theme
        return "\n".join(
            [
                f'BG_COLOR = "{theme.background_color}"',
                f'ACCENT_COLOR = "{theme.accent_color}"',
                f'TEXT_COLOR = "{theme.text_color}"',
                "",
            ]
        )

    def _emit_scene_class(self, class_name: str, scene) -> str:
        ctx = CompileContext()
        body_parts = [
            "self.camera.background_color = BG_COLOR",
            f'scene_title = Text("{scene.scene_name.replace(chr(34), chr(39))}", font_size=1, color=BG_COLOR)',
            "self.add(scene_title)",
        ]
        for block in scene.visual_blocks:
            renderer = self._dispatch[block.block_type]
            body_parts.append(renderer.render_code(block, ctx).rstrip())
        body_parts.append("self.wait(0.2)")
        body = "\n".join(textwrap.indent(part, "        ") for part in body_parts)
        return (
            f"class {class_name}(Scene):\n"
            f"    def construct(self):\n"
            f"{body}\n"
        )

    def _normalize_scene_name(self, scene_title: str, scene_number: int) -> str:
        cleaned = re.sub(r"[^0-9a-zA-Z]+", " ", scene_title).title().replace(" ", "")
        return f"Scene{scene_number:02d}{cleaned or 'Auto'}"
