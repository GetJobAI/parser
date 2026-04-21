from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    text: str
    page: int | None = None
    order: int
    x0: float | None = None
    y0: float | None = None
    x1: float | None = None
    y1: float | None = None


class ResumeMeta(BaseModel):
    original_filename: str | None = None
    mime_type: str | None = None
    parser_version: str = "v1"
    parse_status: Literal["processing", "completed", "failed"] = "processing"
    parse_error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    ocr_used: bool = False
    partial_parse: bool = False
    layout_detected: str | None = None
    extraction_method: str | None = None


class ContactInfo(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None
    raw_text: str | None = None


class SummarySection(BaseModel):
    raw_text: str | None = None


class ExperienceEntry(BaseModel):
    title: str | None = None
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    date_range_raw: str | None = None
    location: str | None = None
    bullets: list[str] = Field(default_factory=list)
    description_raw: str | None = None
    raw_text: str | None = None


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    date_range_raw: str | None = None
    location: str | None = None
    raw_text: str | None = None


class GenericListSection(BaseModel):
    items: list[str] = Field(default_factory=list)
    raw_text: str | None = None


class ResumeContent(BaseModel):
    meta: ResumeMeta = Field(default_factory=ResumeMeta)
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: SummarySection = Field(default_factory=SummarySection)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: GenericListSection = Field(default_factory=GenericListSection)
    certifications: GenericListSection = Field(default_factory=GenericListSection)
    languages: GenericListSection = Field(default_factory=GenericListSection)
    projects: GenericListSection = Field(default_factory=GenericListSection)
    unassigned_blocks: list[str] = Field(default_factory=list)

    @classmethod
    def build_processing(
        cls,
        *,
        filename: str,
        mime_type: str,
        parser_version: str,
    ) -> "ResumeContent":
        return cls(
            meta=ResumeMeta(
                original_filename=filename,
                mime_type=mime_type,
                parser_version=parser_version,
                parse_status="processing",
            ),
        )


class ExtractionResult(BaseModel):
    blocks: list[TextBlock] = Field(default_factory=list)
    extraction_method: str
    warnings: list[str] = Field(default_factory=list)
    ocr_candidate: bool = False


class SectionMatch(BaseModel):
    canonical_name: str
    block_order: int
    score: float
    source_text: str
