from app.detectors.section_detector import detect_section_headers
from app.preprocess.cleaner import preprocess_blocks
from app.schemas.content import TextBlock


def test_preprocess_splits_embedded_headers_and_inline_bullets() -> None:
    blocks = [
        TextBlock(
            text=(
                "SUMMARY Hands-on carpenter with strong workshop discipline. "
                "EXPERIENCE Drewno & Forma 03.2018 – Present Master Carpenter "
                "• Built bespoke furniture • Reduced waste by 18%"
            ),
            order=0,
            page=1,
        )
    ]

    cleaned = preprocess_blocks(blocks)
    header_matches = detect_section_headers(cleaned)

    assert [match.canonical_name for match in header_matches] == ["summary", "experience"]
    assert any(block.text == "- Built bespoke furniture" for block in cleaned)
    assert any(block.text == "- Reduced waste by 18%" for block in cleaned)


def test_preprocess_keeps_first_inline_item_as_bullet_when_source_starts_with_bullet() -> None:
    blocks = [
        TextBlock(
            text="• Design and build bespoke furniture. • Operate CNC router. • Reduce waste.",
            order=0,
            page=1,
        )
    ]

    cleaned = preprocess_blocks(blocks)

    assert [block.text for block in cleaned] == [
        "- Design and build bespoke furniture.",
        "- Operate CNC router.",
        "- Reduce waste.",
    ]
