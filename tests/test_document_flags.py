from app.preprocess.cleaner import detect_repeated_headers_footers
from app.preprocess.layout import detect_layout_and_reorder
from app.schemas.content import TextBlock


def test_detect_repeated_headers_footers_flags_repeated_page_noise() -> None:
    blocks = [
        TextBlock(text="Jane Doe Resume", page=1, order=0, x0=10, y0=10, x1=120, y1=20),
        TextBlock(text="Experience", page=1, order=1, x0=10, y0=80, x1=120, y1=100),
        TextBlock(text="Page 1", page=1, order=2, x0=10, y0=780, x1=50, y1=790),
        TextBlock(text="Jane Doe Resume", page=2, order=3, x0=10, y0=10, x1=120, y1=20),
        TextBlock(text="Education", page=2, order=4, x0=10, y0=80, x1=120, y1=100),
        TextBlock(text="Page 2", page=2, order=5, x0=10, y0=780, x1=50, y1=790),
    ]

    assert detect_repeated_headers_footers(blocks) is True


def test_layout_detection_sets_complex_layout_for_two_column_pages() -> None:
    blocks = [
        TextBlock(text="A", page=1, order=0, x0=10, y0=10, x1=90, y1=20),
        TextBlock(text="B", page=1, order=1, x0=12, y0=40, x1=92, y1=50),
        TextBlock(text="C", page=1, order=2, x0=14, y0=70, x1=94, y1=80),
        TextBlock(text="D", page=1, order=3, x0=220, y0=12, x1=300, y1=22),
        TextBlock(text="E", page=1, order=4, x0=222, y0=42, x1=302, y1=52),
        TextBlock(text="F", page=1, order=5, x0=224, y0=72, x1=304, y1=82),
    ]

    result = detect_layout_and_reorder(blocks)

    assert result.layout_detected == "two_column"
    assert result.has_complex_layout is True
