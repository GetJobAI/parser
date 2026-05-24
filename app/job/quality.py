from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.job_posting import JobPostingContent


class JobPostingQualityReport(BaseModel):
    warnings: list[str] = Field(default_factory=list)
    partial_parse: bool = False
    major_sections_found: list[str] = Field(default_factory=list)


class JobPostingQualityChecker:
    def evaluate(self, content: JobPostingContent) -> JobPostingQualityReport:
        warnings: list[str] = []
        major_sections_found: list[str] = []

        if content.title:
            major_sections_found.append("title")
        if content.company:
            major_sections_found.append("company")
        if content.summary:
            major_sections_found.append("summary")
        if content.responsibilities:
            major_sections_found.append("responsibilities")
        if content.requirements:
            major_sections_found.append("requirements")
        if content.preferred_requirements:
            major_sections_found.append("preferred_requirements")
        if content.benefits:
            major_sections_found.append("benefits")
        if content.skills:
            major_sections_found.append("skills")

        if not content.title:
            warnings.append("No clear job title was detected.")
        if not any([content.requirements, content.responsibilities]):
            warnings.append("Neither responsibilities nor requirements were confidently detected.")
        if content.raw_text and len(content.raw_text) > 250 and len(major_sections_found) < 3:
            warnings.append("Job posting text was substantial, but only a small part was structured.")

        return JobPostingQualityReport(
            warnings=list(dict.fromkeys(warnings)),
            partial_parse=bool(warnings),
            major_sections_found=major_sections_found,
        )
