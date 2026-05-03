from __future__ import annotations

from dataclasses import dataclass

from app.services.video.manim_spec import (
    AxesPlotBlock,
    BulletBuildBlock,
    ComparisonTableBlock,
    EquationStepBlock,
    FlowDiagramBlock,
    HighlightDefinitionBlock,
    TitleCardBlock,
)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


@dataclass(frozen=True)
class CompileContext:
    scene_var: str = "self"


class TitleCardTemplate:
    def render_code(self, block: TitleCardBlock, context: CompileContext) -> str:
        subtitle = (
            f'subtitle = Text("{_escape(block.subtitle)}", font_size=28, color=TEXT_COLOR).next_to(title, DOWN)\n'
            if block.subtitle
            else "subtitle = None\n"
        )
        subtitle_anim = "self.play(FadeIn(subtitle, shift=UP * 0.2))\n" if block.subtitle else ""
        return (
            f'title = Text("{_escape(block.title)}", font_size=42, color=TEXT_COLOR)\n'
            + subtitle +
            "title_group = VGroup(title) if subtitle is None else VGroup(title, subtitle)\n"
            "title_group.arrange(DOWN, buff=0.35).move_to(ORIGIN)\n"
            "self.play(Write(title))\n"
            + subtitle_anim +
            "self.wait(0.4)\n"
        )


class BulletBuildTemplate:
    def render_code(self, block: BulletBuildBlock, context: CompileContext) -> str:
        bullets = ", ".join(
            [f'Text("\\u2022 {_escape(item)}", font_size=28, color=TEXT_COLOR)' for item in block.bullets]
        )
        return (
            f'heading = Text("{_escape(block.heading)}", font_size=36, color=ACCENT_COLOR).to_edge(UP)\n'
            f"bullet_group = VGroup({bullets}).arrange(DOWN, aligned_edge=LEFT, buff=0.35).next_to(heading, DOWN, buff=0.6)\n"
            "self.play(FadeIn(heading, shift=DOWN * 0.2))\n"
            "for bullet in bullet_group:\n"
            "    self.play(FadeIn(bullet, shift=RIGHT * 0.2), run_time=0.5)\n"
            "self.wait(0.3)\n"
        )


class HighlightDefinitionTemplate:
    def render_code(self, block: HighlightDefinitionBlock, context: CompileContext) -> str:
        return (
            f'term = Text("{_escape(block.term)}", font_size=40, color=ACCENT_COLOR).to_edge(UP)\n'
            f'definition = Paragraph("{_escape(block.definition)}", alignment="left", font_size=28, color=TEXT_COLOR).next_to(term, DOWN, buff=0.5)\n'
            "frame = SurroundingRectangle(definition, color=ACCENT_COLOR, buff=0.25)\n"
            "self.play(FadeIn(term, shift=DOWN * 0.2))\n"
            "self.play(Create(frame), FadeIn(definition, shift=UP * 0.2))\n"
            "self.wait(0.3)\n"
        )


class EquationStepTemplate:
    def render_code(self, block: EquationStepBlock, context: CompileContext) -> str:
        title_code = (
            f'title = Text("{_escape(block.title)}", font_size=34, color=ACCENT_COLOR).to_edge(UP)\nself.play(FadeIn(title, shift=DOWN * 0.2))\n'
            if block.title
            else ""
        )
        steps = ", ".join(
            [f'Text("{_escape(step)}", font_size=30, color=TEXT_COLOR)' for step in block.steps]
        )
        anchor = "title" if block.title else "Text('', font_size=1).to_edge(UP)"
        return (
            title_code
            + f"steps_group = VGroup({steps}).arrange(DOWN, buff=0.4).next_to({anchor}, DOWN, buff=0.6)\n"
            + "for step in steps_group:\n"
            + "    self.play(Write(step), run_time=0.6)\n"
            + "self.wait(0.3)\n"
        )


class AxesPlotTemplate:
    def render_code(self, block: AxesPlotBlock, context: CompileContext) -> str:
        x_range = block.x_range or (min(p.x for p in block.points), max(p.x for p in block.points))
        y_range = block.y_range or (min(p.y for p in block.points), max(p.y for p in block.points))
        points = ", ".join([f"Dot(axes.c2p({p.x}, {p.y}), color=ACCENT_COLOR)" for p in block.points])
        title_code = (
            f'title = Text("{_escape(block.title)}", font_size=34, color=ACCENT_COLOR).to_edge(UP)\nself.play(FadeIn(title, shift=DOWN * 0.2))\n'
            if block.title
            else ""
        )
        anchor = "title" if block.title else "ORIGIN"
        return (
            title_code
            + f"axes = Axes(x_range=[{x_range[0]}, {x_range[1]}, 1], y_range=[{y_range[0]}, {y_range[1]}, 1], x_length=8, y_length=4.5, axis_config={{'color': TEXT_COLOR}})\n"
            + f'labels = axes.get_axis_labels(Text("{_escape(block.x_label)}", font_size=24), Text("{_escape(block.y_label)}", font_size=24))\n'
            + "plot_group = VGroup(axes, labels).scale(0.9)\n"
            + ("" if block.title else "plot_group.move_to(ORIGIN)\n")
            + ("plot_group.next_to(title, DOWN, buff=0.6)\n" if block.title else "")
            + "self.play(Create(axes), FadeIn(labels))\n"
            + f"for point in [{points}]:\n"
            + "    self.play(FadeIn(point, scale=0.7), run_time=0.25)\n"
            + "self.wait(0.3)\n"
        )


class FlowDiagramTemplate:
    def render_code(self, block: FlowDiagramBlock, context: CompileContext) -> str:
        title_code = (
            f'title = Text("{_escape(block.title)}", font_size=34, color=ACCENT_COLOR).to_edge(UP)\nself.play(FadeIn(title, shift=DOWN * 0.2))\n'
            if block.title
            else ""
        )
        nodes = ", ".join(
            [
                f'RoundedRectangle(corner_radius=0.12, width=2.2, height=1.0, color=ACCENT_COLOR).add(Text("{_escape(node)}", font_size=24, color=TEXT_COLOR).move_to(ORIGIN))'
                for node in block.nodes
            ]
        )
        return (
            title_code
            + f"nodes = VGroup({nodes}).arrange(RIGHT, buff=0.8)\n"
            + ("nodes.next_to(title, DOWN, buff=1.0)\n" if block.title else "nodes.move_to(ORIGIN)\n")
            + "self.play(LaggedStart(*[FadeIn(node, shift=UP * 0.2) for node in nodes], lag_ratio=0.15))\n"
            + "arrows = VGroup(*[Arrow(nodes[i].get_right(), nodes[i + 1].get_left(), buff=0.15, color=TEXT_COLOR) for i in range(len(nodes) - 1)])\n"
            + "self.play(LaggedStart(*[GrowArrow(arrow) for arrow in arrows], lag_ratio=0.1))\n"
            + "self.wait(0.3)\n"
        )


class ComparisonTableTemplate:
    def render_code(self, block: ComparisonTableBlock, context: CompileContext) -> str:
        title_code = (
            f'title = Text("{_escape(block.title)}", font_size=34, color=ACCENT_COLOR).to_edge(UP)\nself.play(FadeIn(title, shift=DOWN * 0.2))\n'
            if block.title
            else ""
        )
        table_data = [block.headers] + block.rows
        table_repr = repr(table_data)
        return (
            title_code
            + f"table = Table({table_repr}, include_outer_lines=True).scale(0.45)\n"
            + ("table.next_to(title, DOWN, buff=0.6)\n" if block.title else "table.move_to(ORIGIN)\n")
            + "for cell in table.get_entries():\n"
            + "    cell.set_color(TEXT_COLOR)\n"
            + "self.play(Create(table))\n"
            + "self.wait(0.3)\n"
        )
