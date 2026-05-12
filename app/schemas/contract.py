from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.content import ResumeContent


class ResumeContentContractResponse(BaseModel):
    content_schema: dict[str, Any] = Field(
        description="JSON schema of the content object stored in resumes.content."
    )
    content_example: dict[str, Any] = Field(
        description="Example of a valid content payload in the current backend contract."
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Human-readable notes for frontend integration.",
    )


def build_resume_content_contract() -> ResumeContentContractResponse:
    example = ResumeContent(
        meta={
            "original_filename": "resume.pdf",
            "mime_type": "application/pdf",
            "parser_version": "v1",
            "parse_status": "completed",
            "parse_error": None,
            "warnings": [],
            "fallback_used": False,
            "ocr_used": False,
            "partial_parse": False,
            "layout_detected": "single_column",
            "extraction_method": "pymupdf",
        },
        contact={
            "full_name": "Maria Kovalenko",
            "email": "maria@example.com",
            "phone": "+49 123 456789",
            "location": "Berlin, DE",
            "linkedin": "https://linkedin.com/in/maria-kovalenko",
            "github": "https://github.com/maria-kovalenko",
            "website": "https://maria.dev",
            "raw_text": "Maria Kovalenko | Berlin, DE | maria@example.com | +49 123 456789",
        },
        summary={
            "raw_text": "Results-driven product manager with 6+ years of experience."
        },
        experience=[
            {
                "title": "Senior Product Manager",
                "company": "Acme GmbH",
                "start_date": "2021-03",
                "end_date": None,
                "date_range_raw": "2021-03 - Present",
                "location": "Berlin, DE",
                "bullets": [
                    "Grew MAU by 40% after launching onboarding redesign in Q2 2023."
                ],
                "description_raw": None,
                "raw_text": "Senior Product Manager at Acme GmbH, Berlin, DE",
            }
        ],
        education=[
            {
                "institution": "KPI Kyiv",
                "degree": "MSc",
                "field": "Computer Science",
                "start_date": "2016-09",
                "end_date": "2018-06",
                "date_range_raw": "2016-09 - 2018-06",
                "location": "Kyiv, UA",
                "raw_text": "KPI Kyiv, MSc in Computer Science",
            }
        ],
        skills={
            "items": ["Product Strategy", "SQL", "A/B Testing"],
            "raw_text": "Product Strategy, SQL, A/B Testing",
        },
        certifications={
            "items": ["AWS Cloud Practitioner"],
            "raw_text": "AWS Cloud Practitioner",
        },
        languages={
            "items": ["Ukrainian - Native", "English - C1", "German - B2"],
            "raw_text": "Ukrainian - Native; English - C1; German - B2",
        },
        projects={
            "items": ["Open Source CLI Tool"],
            "raw_text": "Open Source CLI Tool - npm tool for internal automation",
        },
        unassigned_blocks=[],
    )

    return ResumeContentContractResponse(
        content_schema=ResumeContent.model_json_schema(),
        content_example=example.model_dump(mode="json"),
        notes=[
            "This contract describes the JSON stored in resumes.content.",
            "The current backend does not expose a separate GET /resumes/{id} endpoint yet.",
            "summary is an object with raw_text, not a plain string.",
            "skills, certifications, languages, and projects use {items, raw_text}.",
            "meta and unassigned_blocks are part of the stored content contract.",
        ],
    )
