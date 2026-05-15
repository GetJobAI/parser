from __future__ import annotations

import re

from app.schemas.content import SectionMatch, TextBlock
from app.utils.fuzzy import best_fuzzy_match

SECTION_SYNONYMS: dict[str, list[str]] = {
    "contact": ["contact", "contact information", "personal information", "personal details"],
    "summary": ["summary", "profile", "about", "professional summary", "objective"],
    "experience": ["experience", "work experience", "employment", "work history", "career history"],
    "education": ["education", "academic background", "qualifications", "ekucation"],
    "skills": [
        "skills",
        "technical skills",
        "competencies",
        "expertise",
        "core competencies",
        "skils",
    ],
    "certifications": ["certifications", "licenses", "certificates"],
    "languages": ["languages", "language proficiency"],
    "projects": ["projects", "selected projects", "project experience"],
}

HEADER_SANITIZE_RE = re.compile(r"[^a-z0-9/&+\- ]+", re.IGNORECASE)


def detect_section_headers(blocks: list[TextBlock]) -> list[SectionMatch]:
    matches: list[SectionMatch] = []
    last_order = -10

    for block in blocks:
        text = block.text.strip()
        if not _is_candidate_header(text):
            continue

        normalized = HEADER_SANITIZE_RE.sub("", text.lower()).strip()
        best_name = ""
        best_score = 0.0

        for canonical_name, variants in SECTION_SYNONYMS.items():
            _, score = best_fuzzy_match(normalized, variants)
            if score > best_score:
                best_name = canonical_name
                best_score = score

        if best_score < 84:
            continue
        if block.order - last_order <= 1 and matches and matches[-1].canonical_name == best_name:
            continue

        matches.append(
            SectionMatch(
                canonical_name=best_name,
                block_order=block.order,
                score=best_score,
                source_text=text,
            )
        )
        last_order = block.order

    return matches


def _is_candidate_header(text: str) -> bool:
    if not text:
        return False
    if len(text) > 48:
        return False
    if len(text.split()) > 5:
        return False
    lower_text = text.lower()
    if any(marker in lower_text for marker in ("@", "http://", "https://", ".com", ".io")):
        return False
    if any(char.isdigit() for char in text):
        return False
    return True
