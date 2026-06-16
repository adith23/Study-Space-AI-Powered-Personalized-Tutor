"""
Unit tests for the Manim Pro code generator.

Tests cover response parsing, scene name extraction, markdown fence
stripping, and prompt construction — without requiring a live LLM.
"""

from __future__ import annotations

import pytest

from app.services.video.manim_pro_code_generator import (
    _build_user_prompt,
    _extract_scene_names,
    _strip_markdown_fences,
)

# ── _strip_markdown_fences ───────────────────────────────────────────────────


class TestStripMarkdownFences:
    def test_plain_code_unchanged(self):
        code = "from manim import *\n\nclass Scene01(Scene):\n    pass"
        assert _strip_markdown_fences(code) == code.strip()

    def test_python_fences_removed(self):
        wrapped = "```python\nfrom manim import *\nclass Scene01(Scene):\n    pass\n```"
        expected = "from manim import *\nclass Scene01(Scene):\n    pass"
        assert _strip_markdown_fences(wrapped) == expected

    def test_plain_fences_removed(self):
        wrapped = "```\nfrom manim import *\n```"
        expected = "from manim import *"
        assert _strip_markdown_fences(wrapped) == expected

    def test_whitespace_handling(self):
        wrapped = "  ```python\n  code here\n  ```  "
        result = _strip_markdown_fences(wrapped)
        assert "```" not in result
        assert "code here" in result


# ── _extract_scene_names ─────────────────────────────────────────────────────


class TestExtractSceneNames:
    def test_standard_scene_names(self):
        code = (
            "from manim import *\n\n"
            "class Scene01(Scene):\n    pass\n\n"
            "class Scene02(Scene):\n    pass\n\n"
            "class Scene03(Scene):\n    pass\n"
        )
        names = _extract_scene_names(code)
        assert names == ["Scene01", "Scene02", "Scene03"]

    def test_named_scenes(self):
        code = (
            "from manim import *\n\n"
            "class Scene01Introduction(Scene):\n    pass\n\n"
            "class Scene02MainConcept(Scene):\n    pass\n"
        )
        names = _extract_scene_names(code)
        assert names == ["Scene01Introduction", "Scene02MainConcept"]

    def test_no_scenes_returns_empty(self):
        code = "from manim import *\n\ndef helper():\n    pass\n"
        names = _extract_scene_names(code)
        assert names == []

    def test_fallback_to_generic_scene_classes(self):
        code = (
            "from manim import *\n\n"
            "class MyIntro(Scene):\n    pass\n\n"
            "class MyConclusion(Scene):\n    pass\n"
        )
        names = _extract_scene_names(code)
        assert names == ["MyIntro", "MyConclusion"]

    def test_moving_camera_scene_fallback(self):
        code = "from manim import *\n\nclass ZoomScene(MovingCameraScene):\n    pass\n"
        names = _extract_scene_names(code)
        assert names == ["ZoomScene"]

    def test_three_d_scene_fallback(self):
        code = "from manim import *\n\nclass My3D(ThreeDScene):\n    pass\n"
        names = _extract_scene_names(code)
        assert names == ["My3D"]

    def test_ignores_non_scene_classes(self):
        code = (
            "from manim import *\n\n"
            "class Helper:\n    pass\n\n"
            "class Scene01(Scene):\n    pass\n"
        )
        names = _extract_scene_names(code)
        assert names == ["Scene01"]


# ── _build_user_prompt ───────────────────────────────────────────────────────


class TestBuildUserPrompt:
    @pytest.fixture()
    def mock_script(self):
        from app.schemas.video_schema import VideoScene, VideoScript

        return VideoScript(
            title="Test Video",
            total_duration_seconds=45.0,
            scenes=[
                VideoScene(
                    scene_number=1,
                    narration_text="This is scene one narration.",
                    visual_description="A title card.",
                    duration_seconds=15.0,
                    key_concept="Introduction",
                ),
                VideoScene(
                    scene_number=2,
                    narration_text="This is scene two narration.",
                    visual_description="A diagram.",
                    duration_seconds=30.0,
                    key_concept="Main Concept",
                ),
            ],
        )

    @pytest.fixture()
    def mock_context(self):
        from app.services.content_generation_context_service import (
            ContentGenerationContext,
        )
        from app.models.quiz_model import QuizGenerationMode

        return ContentGenerationContext(
            mode=QuizGenerationMode.BROAD_FULL_SOURCE,
            context_text="Sample educational content about photosynthesis.",
        )

    def test_includes_script_title(self, mock_script, mock_context):
        prompt = _build_user_prompt(
            script=mock_script,
            context=mock_context,
            style="explainer",
            focus_prompt=None,
        )
        assert "Test Video" in prompt

    def test_includes_narration_text(self, mock_script, mock_context):
        prompt = _build_user_prompt(
            script=mock_script,
            context=mock_context,
            style="explainer",
            focus_prompt=None,
        )
        assert "This is scene one narration." in prompt
        assert "This is scene two narration." in prompt

    def test_includes_context(self, mock_script, mock_context):
        prompt = _build_user_prompt(
            script=mock_script,
            context=mock_context,
            style="explainer",
            focus_prompt=None,
        )
        assert "photosynthesis" in prompt

    def test_includes_focus_prompt(self, mock_script, mock_context):
        prompt = _build_user_prompt(
            script=mock_script,
            context=mock_context,
            style="explainer",
            focus_prompt="Focus on the Calvin cycle",
        )
        assert "Focus on the Calvin cycle" in prompt

    def test_broad_focus_when_no_prompt(self, mock_script, mock_context):
        prompt = _build_user_prompt(
            script=mock_script,
            context=mock_context,
            style="explainer",
            focus_prompt=None,
        )
        assert "cover the material broadly" in prompt

    def test_style_instruction_summary(self, mock_script, mock_context):
        prompt = _build_user_prompt(
            script=mock_script,
            context=mock_context,
            style="summary",
            focus_prompt=None,
        )
        assert "concise summary" in prompt

    def test_style_instruction_deep_dive(self, mock_script, mock_context):
        prompt = _build_user_prompt(
            script=mock_script,
            context=mock_context,
            style="deep_dive",
            focus_prompt=None,
        )
        assert "deep-dive" in prompt

    def test_includes_key_concepts(self, mock_script, mock_context):
        prompt = _build_user_prompt(
            script=mock_script,
            context=mock_context,
            style="explainer",
            focus_prompt=None,
        )
        assert "Introduction" in prompt
        assert "Main Concept" in prompt
