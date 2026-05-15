from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field


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


class HeadingOverrides(BaseModel):
    summary: str | None = None
    experience: str | None = None
    education: str | None = None
    skills: str | None = None
    certifications: str | None = None
    projects: str | None = None
    languages: str | None = None


class ContactInfo(BaseModel):
    name: str | None = Field(default=None, validation_alias=AliasChoices("name", "full_name"))
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None


class ExperienceEntry(BaseModel):
    company: str | None = None
    title: str | None = None
    dates: str | None = None
    location: str | None = None
    bullets: list[str] = Field(default_factory=list)
    hide: bool = False


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    dates: str | None = None
    location: str | None = None
    grade: str | None = None
    hide: bool = False


class SkillGroup(BaseModel):
    category: str
    items: list[str] = Field(default_factory=list)


class CertificationEntry(BaseModel):
    name: str | None = None
    issuer: str | None = None
    date: str | None = None


class LanguageEntry(BaseModel):
    name: str | None = None
    level: str | None = None


class ProjectEntry(BaseModel):
    name: str | None = None
    description: str | None = None
    url: str | None = None


class ResumeContent(BaseModel):
    style: Literal["professional", "minimal", "technical"] | None = None
    headings: HeadingOverrides | None = None
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str | None = None
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[SkillGroup] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    meta: ResumeMeta = Field(default_factory=ResumeMeta)
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
