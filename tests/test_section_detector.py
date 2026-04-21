from app.detectors.section_detector import detect_section_headers
from app.schemas.content import TextBlock


def test_detects_fuzzy_section_headers() -> None:
    blocks = [
        TextBlock(text="Jane Doe", order=0),
        TextBlock(text="Experiance", order=1),
        TextBlock(text="Software Engineer", order=2),
        TextBlock(text="Ekucation", order=3),
    ]

    matches = detect_section_headers(blocks)

    assert [match.canonical_name for match in matches] == ["experience", "education"]
