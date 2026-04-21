from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.content import ResumeContent, TextBlock


class QualityReport(BaseModel):
    warnings: list[str] = Field(default_factory=list)
    partial_parse: bool = False
    major_sections_found: list[str] = Field(default_factory=list)


class QualityChecker:
    def evaluate(self, content: ResumeContent, extracted_blocks: list[TextBlock]) -> QualityReport:
        warnings: list[str] = []
        major_sections_found: list[str] = []

        if any(
            [
                content.contact.full_name,
                content.contact.email,
                content.contact.phone,
                content.contact.linkedin,
                content.contact.github,
                content.contact.website,
            ]
        ):
            major_sections_found.append("contact")
        if content.summary.raw_text:
            major_sections_found.append("summary")
        if content.experience:
            major_sections_found.append("experience")
        if content.education:
            major_sections_found.append("education")
        if content.skills.items or content.skills.raw_text:
            major_sections_found.append("skills")
        if content.certifications.items or content.certifications.raw_text:
            major_sections_found.append("certifications")
        if content.languages.items or content.languages.raw_text:
            major_sections_found.append("languages")
        if content.projects.items or content.projects.raw_text:
            major_sections_found.append("projects")

        if not any([content.contact.email, content.contact.phone, content.contact.linkedin, content.contact.github]):
            warnings.append("No strong contact details were detected.")
        if not major_sections_found:
            warnings.append("No major resume sections were confidently detected.")

        unassigned_ratio = len(content.unassigned_blocks) / max(1, len(extracted_blocks))
        if unassigned_ratio > 0.35:
            warnings.append("A large share of the document remained unassigned.")

        extracted_text_size = sum(len(block.text) for block in extracted_blocks)
        meaningful_output = bool(major_sections_found or content.unassigned_blocks)
        if extracted_text_size > 200 and not meaningful_output:
            warnings.append("Extracted text was non-trivial, but the structured result is almost empty.")

        partial_parse = bool(warnings)
        return QualityReport(
            warnings=list(dict.fromkeys(warnings)),
            partial_parse=partial_parse,
            major_sections_found=major_sections_found,
        )
