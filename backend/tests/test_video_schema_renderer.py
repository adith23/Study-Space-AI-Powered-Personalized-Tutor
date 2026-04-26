from app.schemas.video_schema import VideoGenerateRequest


def test_renderer_defaults_to_image():
    payload = VideoGenerateRequest(file_ids=[1, 2])
    assert payload.renderer == "image"
