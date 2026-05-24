from app.schemas.response import ParseResumeResponse


def test_parse_resume_response_exposes_parsing_flags() -> None:
    response = ParseResumeResponse(
        resume_id="resume-123",
        parse_status="completed",
        partial_parse=False,
        fallback_used=True,
        ocr_used=False,
        extraction_method="pymupdf",
        layout_detected="single_column",
        has_complex_layout=False,
        has_graphics=True,
        has_headers_footers=False,
        has_non_standard_fonts=True,
        event_published=True,
        warnings=[],
        major_sections_found=["contact", "experience"],
    )

    assert response.parse_status == "completed"
    assert response.fallback_used is True
    assert response.ocr_used is False
    assert response.extraction_method == "pymupdf"
    assert response.layout_detected == "single_column"
    assert response.has_complex_layout is False
    assert response.has_graphics is True
    assert response.has_headers_footers is False
    assert response.has_non_standard_fonts is True
    assert response.event_published is True
