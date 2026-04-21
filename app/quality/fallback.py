from __future__ import annotations

from app.parsers.contact_parser import ContactParser
from app.parsers.education_parser import EducationParser
from app.parsers.experience_parser import ExperienceParser
from app.parsers.skills_parser import SkillsParser
from app.schemas.content import ResumeContent, TextBlock
from app.utils.text import blocks_to_text


class FallbackManager:
    """
    Secondary, deterministic rescue path.

    This is where future OCR and selective AI hooks can be added without changing
    the main rules-first pipeline. The MVP keeps fallback mechanical and conservative.
    """

    def __init__(self) -> None:
        self._contact_parser = ContactParser()
        self._experience_parser = ExperienceParser()
        self._education_parser = EducationParser()
        self._skills_parser = SkillsParser()

    def apply(
        self,
        content: ResumeContent,
        all_blocks: list[TextBlock],
    ) -> ResumeContent:
        warnings: list[str] = []
        fallback_used = False

        if self._contact_is_weak(content):
            candidate_blocks = all_blocks[:6]
            reparsed_contact = self._contact_parser.parse(candidate_blocks)
            if any(
                [
                    reparsed_contact.email,
                    reparsed_contact.phone,
                    reparsed_contact.linkedin,
                    reparsed_contact.github,
                ]
            ):
                content.contact = reparsed_contact
                fallback_used = True
                warnings.append("Fallback contact parsing used the document header area.")

        if not content.experience:
            experience_blocks = [block for block in all_blocks if _looks_like_experience(block.text)]
            if experience_blocks:
                content.experience = self._experience_parser.parse(experience_blocks)
                fallback_used = True
                warnings.append("Fallback heuristics inferred an experience section.")

        if not content.education:
            education_blocks = [block for block in all_blocks if _looks_like_education(block.text)]
            if education_blocks:
                content.education = self._education_parser.parse(education_blocks)
                fallback_used = True
                warnings.append("Fallback heuristics inferred an education section.")

        if not content.skills.items and not content.skills.raw_text:
            skills_blocks = [block for block in all_blocks if _looks_like_skills(block.text)]
            if skills_blocks:
                content.skills = self._skills_parser.parse(skills_blocks)
                fallback_used = True
                warnings.append("Fallback heuristics inferred a skills section.")

        if fallback_used:
            content.meta.fallback_used = True
            content.meta.warnings.extend(warnings)

        return content

    def _contact_is_weak(self, content: ResumeContent) -> bool:
        return not any(
            [
                content.contact.email,
                content.contact.phone,
                content.contact.linkedin,
                content.contact.github,
                content.contact.website,
            ]
        )


def _looks_like_experience(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in ("experience", "engineer", "developer", "manager")) or (
        any(token in lowered for token in ("present", "current"))
        and any(char.isdigit() for char in text)
    )


def _looks_like_education(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in ("university", "college", "school", "bachelor", "master"))


def _looks_like_skills(text: str) -> bool:
    lowered = text.lower()
    return (
        any(keyword in lowered for keyword in ("skills", "technologies", "tools"))
        or text.count(",") >= 3
        or "|" in text
    )
