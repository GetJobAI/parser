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
        style="professional",
        headings={
            "summary": "Summary",
            "experience": "Experience",
            "education": "Education",
            "skills": "Skills",
            "certifications": "Certifications",
            "projects": "Projects",
            "languages": "Languages",
        },
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
            "name": "Example Candidate",
            "email": "candidate@example.com",
            "phone": "+49 000 000000",
            "location": "Berlin, DE",
            "linkedin": "linkedin.com/in/example-candidate",
            "github": "github.com/example-candidate",
        },
        summary="Results-driven product manager with 6+ years of experience.",
        experience=[
            {
                "company": "Acme GmbH",
                "title": "Senior Product Manager",
                "dates": "03.2021 – present",
                "location": "Berlin, DE",
                "bullets": [
                    "Grew MAU by 40% after launching onboarding redesign in Q2 2023."
                ],
                "hide": False,
            }
        ],
        education=[
            {
                "institution": "KPI Kyiv",
                "degree": "MSc — Computer Science",
                "dates": "09.2016 – 06.2018",
                "location": "Kyiv, UA",
                "grade": "5.0 / 5.0",
                "hide": False,
            }
        ],
        skills=[
            {"category": "Product", "items": ["Product Strategy", "A/B Testing"]},
            {"category": "Technical", "items": ["SQL"]},
        ],
        certifications=[
            {"name": "AWS Cloud Practitioner", "issuer": "Amazon Web Services", "date": "11.2023"},
        ],
        languages=[
            {"name": "Ukrainian", "level": "Native"},
            {"name": "English", "level": "C1"},
            {"name": "German", "level": "B2"},
        ],
        projects=[
            {
                "name": "Open Source CLI Tool",
                "description": "npm tool for internal automation",
                "url": "github.com/example-candidate/cli-tool",
            }
        ],
        unassigned_blocks=[],
    )

    return ResumeContentContractResponse(
        content_schema=ResumeContent.model_json_schema(),
        content_example=example.model_dump(mode="json"),
        notes=[
            "This contract describes the JSON stored in resumes.content.",
            "The current backend does not expose a separate GET /resumes/{id} endpoint yet.",
            "The resume data shape follows the template repository schema.",
            "summary is stored as a plain string.",
            "skills use grouped entries with {category, items}.",
            "certifications, languages, and projects use structured arrays.",
            "meta and unassigned_blocks are part of the stored content contract.",
        ],
    )
