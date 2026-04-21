from pydantic import BaseModel, Field


class ParseResumeResponse(BaseModel):
    resume_id: str
    partial_parse: bool
    warnings: list[str] = Field(default_factory=list)
    major_sections_found: list[str] = Field(default_factory=list)
