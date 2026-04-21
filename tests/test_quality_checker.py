from app.quality.checker import QualityChecker
from app.schemas.content import ContactInfo, ResumeContent, SummarySection, TextBlock


def test_quality_checker_flags_missing_contact_details() -> None:
    checker = QualityChecker()
    content = ResumeContent(
        contact=ContactInfo(full_name="Jane Doe"),
        summary=SummarySection(raw_text="Experienced engineer."),
    )
    blocks = [TextBlock(text="Jane Doe", order=0), TextBlock(text="Experienced engineer.", order=1)]

    report = checker.evaluate(content, blocks)

    assert report.partial_parse is True
    assert "summary" in report.major_sections_found
    assert any("contact" in warning.lower() for warning in report.warnings)
