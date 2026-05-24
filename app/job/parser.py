from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from app.schemas.job_posting import JobPostingContent
from app.utils.text import collapse_whitespace, compact_lines

SECTION_ALIASES = {
    "summary": {
        "about the role",
        "about the job",
        "job summary",
        "summary",
        "overview",
        "description",
        "position overview",
        "about us",
    },
    "responsibilities": {
        "responsibilities",
        "what you'll do",
        "what you will do",
        "your responsibilities",
        "duties",
        "tasks",
        "day to day",
        "day-to-day",
        "what you’ll do",
    },
    "requirements": {
        "requirements",
        "qualifications",
        "required qualifications",
        "minimum qualifications",
        "what we're looking for",
        "what we are looking for",
        "your profile",
        "must have",
        "must-have",
        "what you bring",
    },
    "preferred_requirements": {
        "preferred qualifications",
        "preferred",
        "nice to have",
        "nice-to-have",
        "bonus points",
        "pluses",
        "preferred skills",
    },
    "benefits": {
        "benefits",
        "what we offer",
        "perks",
        "why join us",
        "compensation and benefits",
        "offer",
    },
}

SECTION_ORDER = list(SECTION_ALIASES.keys())
LOCATION_RE = re.compile(
    r"\b(remote|hybrid|on-site|onsite|berlin|warsaw|wroclaw|krakow|london|new york|paris|munich|amsterdam|kyiv|kyiv city|ukraine|poland|germany|usa|europe)\b",
    re.IGNORECASE,
)
TITLE_HINT_RE = re.compile(
    r"\b(engineer|developer|manager|designer|analyst|specialist|consultant|architect|scientist|lead|director|recruiter|marketer|administrator)\b",
    re.IGNORECASE,
)
SENIORITY_PATTERNS = [
    ("principal", re.compile(r"\bprincipal\b", re.IGNORECASE)),
    ("staff", re.compile(r"\bstaff\b", re.IGNORECASE)),
    ("lead", re.compile(r"\blead\b", re.IGNORECASE)),
    ("senior", re.compile(r"\bsenior|sr\.\b", re.IGNORECASE)),
    ("mid", re.compile(r"\bmid(?:-level)?\b", re.IGNORECASE)),
    ("junior", re.compile(r"\bjunior|jr\.\b", re.IGNORECASE)),
    ("intern", re.compile(r"\bintern(ship)?\b", re.IGNORECASE)),
]
EMPLOYMENT_PATTERNS = [
    ("full-time", re.compile(r"\bfull[\s-]?time\b", re.IGNORECASE)),
    ("part-time", re.compile(r"\bpart[\s-]?time\b", re.IGNORECASE)),
    ("contract", re.compile(r"\bcontract|freelance\b", re.IGNORECASE)),
    ("internship", re.compile(r"\bintern(ship)?\b", re.IGNORECASE)),
    ("temporary", re.compile(r"\btemporary|fixed[- ]term\b", re.IGNORECASE)),
]
WORK_MODE_PATTERNS = [
    ("remote", re.compile(r"\bremote\b", re.IGNORECASE)),
    ("hybrid", re.compile(r"\bhybrid\b", re.IGNORECASE)),
    ("on-site", re.compile(r"\bon[- ]site|onsite|in office\b", re.IGNORECASE)),
]
SKILL_KEYWORDS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "Go",
    "Rust",
    "C#",
    "C++",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Docker",
    "Kubernetes",
    "AWS",
    "GCP",
    "Azure",
    "React",
    "Next.js",
    "Node.js",
    "FastAPI",
    "Django",
    "Flask",
    "Spring",
    "Git",
    "CI/CD",
    "Terraform",
    "Linux",
    "GraphQL",
    "REST",
    "HTML",
    "CSS",
    "Figma",
    "Agile",
    "Scrum",
]
SKILL_REGEXES = [(skill, re.compile(rf"(?<!\w){re.escape(skill)}(?!\w)", re.IGNORECASE)) for skill in SKILL_KEYWORDS]


class JobPostingParser:
    def parse(
        self,
        *,
        content: JobPostingContent,
        text: str,
        title_candidates: list[str],
        meta_title: str | None,
        meta_description: str | None,
        structured_data: dict[str, Any] | None,
        salary_hint: str | None,
    ) -> JobPostingContent:
        lines = compact_lines(text.splitlines())
        structured_data = structured_data or {}

        content.raw_text = text
        content.title = self._pick_title(structured_data, title_candidates, meta_title, lines)
        content.company = self._pick_company(structured_data, lines)
        content.location = self._pick_location(structured_data, lines)
        content.employment_type = self._pick_employment_type(structured_data, text)
        content.work_mode = self._pick_work_mode(text)
        content.seniority = self._pick_seniority(content.title, text)
        content.salary = self._pick_salary(structured_data, salary_hint, text)

        intro_lines, sections = self._split_sections(lines)
        content.summary = self._build_summary(structured_data, meta_description, intro_lines)
        content.responsibilities = self._section_items(sections.get("responsibilities", []))
        content.requirements = self._section_items(sections.get("requirements", []))
        content.preferred_requirements = self._section_items(sections.get("preferred_requirements", []))
        content.benefits = self._section_items(sections.get("benefits", []))
        content.skills = self._extract_skills(
            [
                content.title or "",
                content.summary or "",
                *content.requirements,
                *content.preferred_requirements,
                *content.responsibilities,
            ]
        )
        content.unassigned_sections = self._collect_unassigned_sections(sections)
        content.meta.structured_data_used = bool(structured_data)
        return content

    def _pick_title(
        self,
        structured_data: dict[str, Any],
        title_candidates: list[str],
        meta_title: str | None,
        lines: list[str],
    ) -> str | None:
        title = collapse_whitespace(str(structured_data.get("title", "")))
        if title:
            return title
        for candidate in [*title_candidates, meta_title]:
            cleaned = self._clean_title(candidate)
            if cleaned:
                return cleaned
        for line in lines[:5]:
            if self._is_heading_line(line) or line.startswith("- "):
                continue
            if TITLE_HINT_RE.search(line):
                return self._clean_title(line)
        return self._clean_title(lines[0]) if lines else None

    def _pick_company(self, structured_data: dict[str, Any], lines: list[str]) -> str | None:
        company = structured_data.get("hiringOrganization")
        if isinstance(company, dict):
            name = collapse_whitespace(str(company.get("name", "")))
            if name:
                return name
        company_line = structured_data.get("company")
        if isinstance(company_line, str) and collapse_whitespace(company_line):
            return collapse_whitespace(company_line)

        for line in lines[:8]:
            lowered = line.lower()
            if lowered.startswith("company:"):
                return collapse_whitespace(line.split(":", 1)[1])
            if " at " in lowered and TITLE_HINT_RE.search(line):
                return collapse_whitespace(line.split(" at ", 1)[1])

        for line in lines[1:6]:
            if self._is_heading_line(line) or line.startswith("- "):
                continue
            if LOCATION_RE.search(line):
                continue
            if len(line.split()) <= 8 and not TITLE_HINT_RE.search(line):
                return line
        return None

    def _pick_location(self, structured_data: dict[str, Any], lines: list[str]) -> str | None:
        raw_location = structured_data.get("jobLocation")
        location = self._extract_location_from_structured_data(raw_location)
        if location:
            return location
        if isinstance(structured_data.get("applicantLocationRequirements"), dict):
            location = self._extract_location_from_structured_data(structured_data["applicantLocationRequirements"])
            if location:
                return location
        for line in lines[:10]:
            lowered = line.lower()
            if lowered.startswith("location:"):
                return collapse_whitespace(line.split(":", 1)[1])
            if LOCATION_RE.search(line):
                return collapse_whitespace(re.sub(r"(?i)^location:\s*", "", line))
        return None

    def _pick_employment_type(self, structured_data: dict[str, Any], text: str) -> str | None:
        raw = structured_data.get("employmentType")
        if isinstance(raw, list):
            raw = ", ".join(str(item) for item in raw if str(item).strip())
        if isinstance(raw, str) and collapse_whitespace(raw):
            normalized = collapse_whitespace(raw).lower().replace("_", "-")
            return normalized
        for label, pattern in EMPLOYMENT_PATTERNS:
            if pattern.search(text):
                return label
        return None

    def _pick_work_mode(self, text: str) -> str | None:
        for label, pattern in WORK_MODE_PATTERNS:
            if pattern.search(text):
                return label
        return None

    def _pick_seniority(self, title: str | None, text: str) -> str | None:
        combined = f"{title or ''}\n{text}"
        for label, pattern in SENIORITY_PATTERNS:
            if pattern.search(combined):
                return label
        return None

    def _pick_salary(self, structured_data: dict[str, Any], salary_hint: str | None, text: str) -> str | None:
        base_salary = structured_data.get("baseSalary")
        if isinstance(base_salary, dict):
            currency = str(base_salary.get("currency", "")).strip()
            value = base_salary.get("value")
            if isinstance(value, dict):
                min_value = value.get("minValue")
                max_value = value.get("maxValue")
                unit = value.get("unitText")
                pieces = [str(piece) for piece in [min_value, max_value] if piece is not None]
                if pieces:
                    salary = " - ".join(pieces)
                    if currency:
                        salary = f"{currency} {salary}"
                    if unit:
                        salary = f"{salary} / {unit}"
                    return collapse_whitespace(salary)
        if salary_hint:
            return salary_hint
        match = re.search(
            r"(?:(?:USD|EUR|GBP|PLN|UAH|CAD|AUD|CHF)\s*)?(?:\$|€|£)?\s?\d[\d\s,.]*(?:k|K)?\s*(?:-|–|to)\s*(?:\$|€|£)?\s?\d[\d\s,.]*(?:k|K)?",
            text,
            re.IGNORECASE,
        )
        if match:
            return collapse_whitespace(match.group(0))
        return None

    def _split_sections(self, lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
        intro: list[str] = []
        sections: dict[str, list[str]] = {}
        current_section: str | None = None

        for line in lines:
            canonical = self._canonical_section_name(line)
            if canonical:
                current_section = canonical
                sections.setdefault(canonical, [])
                continue
            if current_section:
                sections[current_section].append(line)
            else:
                intro.append(line)
        return intro, sections

    def _build_summary(
        self,
        structured_data: dict[str, Any],
        meta_description: str | None,
        intro_lines: list[str],
    ) -> str | None:
        for key in ("description",):
            value = structured_data.get(key)
            if isinstance(value, str):
                cleaned = self._clean_structured_description(value)
                if cleaned:
                    return cleaned
        if meta_description:
            return meta_description

        summary_lines: list[str] = []
        for line in intro_lines:
            if self._is_heading_line(line):
                continue
            if line.startswith("- "):
                break
            if len(line.split()) <= 2 and not TITLE_HINT_RE.search(line):
                continue
            summary_lines.append(line)
            if sum(len(item) for item in summary_lines) > 420:
                break
        if not summary_lines:
            return None
        return collapse_whitespace(" ".join(summary_lines[:4]))

    def _section_items(self, lines: Iterable[str]) -> list[str]:
        items: list[str] = []
        buffer: list[str] = []
        for line in lines:
            if self._is_heading_line(line):
                continue
            if line.startswith("- "):
                if buffer:
                    items.append(collapse_whitespace(" ".join(buffer)))
                    buffer = []
                items.append(self._normalize_item_text(line[2:]))
                continue
            if self._looks_like_list_item(line):
                if buffer:
                    items.append(collapse_whitespace(" ".join(buffer)))
                    buffer = []
                items.append(self._normalize_item_text(line))
                continue
            buffer.append(line)
        if buffer:
            merged = collapse_whitespace(" ".join(buffer))
            if merged:
                sentence_items = self._split_sentences(merged)
                items.extend(sentence_items if len(sentence_items) > 1 else [self._normalize_item_text(merged)])
        return list(dict.fromkeys(item for item in items if item))

    def _extract_skills(self, texts: Iterable[str]) -> list[str]:
        haystack = "\n".join(texts)
        found: list[str] = []
        for skill, pattern in SKILL_REGEXES:
            if pattern.search(haystack):
                found.append(skill)
        return found

    def _collect_unassigned_sections(self, sections: dict[str, list[str]]) -> list[str]:
        known_sections = {"summary", "responsibilities", "requirements", "preferred_requirements", "benefits"}
        leftovers = []
        for key, lines in sections.items():
            if key not in known_sections and lines:
                leftovers.append(f"{key}: {' '.join(lines)}")
        return leftovers

    def _canonical_section_name(self, line: str) -> str | None:
        normalized = collapse_whitespace(line).lower().strip(":")
        normalized = normalized.replace("’", "'")
        if len(normalized.split()) > 6:
            return None
        for canonical, aliases in SECTION_ALIASES.items():
            if normalized in aliases:
                return canonical
        return None

    def _is_heading_line(self, line: str) -> bool:
        return self._canonical_section_name(line) is not None

    def _looks_like_list_item(self, line: str) -> bool:
        if len(line.split()) > 18:
            return False
        lowered = line.lower()
        if lowered.startswith(("experience with ", "knowledge of ", "ability to ")):
            return True
        return bool(re.match(r"^[A-Z0-9][^:]{0,80}$", line)) and line.endswith((".", ";"))

    def _split_sentences(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        return [self._normalize_item_text(sentence) for sentence in sentences if collapse_whitespace(sentence)]

    def _normalize_item_text(self, text: str) -> str:
        return collapse_whitespace(text).rstrip(".;")

    def _extract_location_from_structured_data(self, value: Any) -> str | None:
        if isinstance(value, list):
            parts = [self._extract_location_from_structured_data(item) for item in value]
            cleaned = [part for part in parts if part]
            return cleaned[0] if cleaned else None
        if not isinstance(value, dict):
            return None
        address = value.get("address")
        if isinstance(address, dict):
            pieces = [
                address.get("addressLocality"),
                address.get("addressRegion"),
                address.get("addressCountry"),
            ]
            cleaned = [collapse_whitespace(str(piece)) for piece in pieces if piece]
            if cleaned:
                return ", ".join(dict.fromkeys(cleaned))
        name = value.get("name")
        if isinstance(name, str) and collapse_whitespace(name):
            return collapse_whitespace(name)
        return None

    def _clean_title(self, value: str | None) -> str | None:
        if not value:
            return None
        cleaned = collapse_whitespace(value)
        cleaned = re.split(r"\s+[|\-–]\s+", cleaned)[0]
        return cleaned or None

    def _clean_structured_description(self, value: str) -> str:
        text = re.sub(r"(?i)<br\s*/?>", "\n", value)
        text = re.sub(r"(?i)</(p|div|li|ul|ol|h1|h2|h3|h4|h5|h6)>", "\n", text)
        text = re.sub(r"(?i)<li\b[^>]*>", "\n- ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = collapse_whitespace(text)
        sentences = self._split_sentences(text)
        return " ".join(sentences[:3]) if sentences else text
