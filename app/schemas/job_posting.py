from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class JobPostingMeta(BaseModel):
    source_url: str | None = None
    parser_version: str = "v1"
    parse_status: Literal["processing", "completed", "failed"] = "processing"
    parse_error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_parse: bool = False
    extraction_method: str | None = None
    html_provided: bool = False
    structured_data_used: bool = False


class JobPostingContent(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    work_mode: str | None = None
    employment_type: str | None = None
    seniority: str | None = None
    summary: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    preferred_requirements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    salary: str | None = None
    meta: JobPostingMeta = Field(default_factory=JobPostingMeta)
    unassigned_sections: list[str] = Field(default_factory=list)
    raw_text: str | None = None

    @classmethod
    def build_processing(
        cls,
        *,
        parser_version: str,
        source_url: str | None = None,
        html_provided: bool = False,
    ) -> "JobPostingContent":
        return cls(
            meta=JobPostingMeta(
                parser_version=parser_version,
                parse_status="processing",
                source_url=source_url,
                html_provided=html_provided,
            )
        )


class ParseJobPostingRequest(BaseModel):
    html: str | None = None
    text: str | None = None
    source_url: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "ParseJobPostingRequest":
        if not (self.html or self.text):
            raise ValueError("Either html or text must be provided.")
        return self


class ParseJobPostingResponse(BaseModel):
    parse_status: str
    partial_parse: bool
    extraction_method: str | None = None
    structured_data_used: bool = False
    warnings: list[str] = Field(default_factory=list)
    major_sections_found: list[str] = Field(default_factory=list)
    content: JobPostingContent
