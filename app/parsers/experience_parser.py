from __future__ import annotations

import re

from app.schemas.content import ExperienceEntry, TextBlock
from app.utils.regexes import extract_date_range, split_date_range
from app.utils.text import blocks_to_text

ROLE_KEYWORDS = {
    "engineer",
    "developer",
    "manager",
    "analyst",
    "designer",
    "consultant",
    "intern",
    "specialist",
    "lead",
    "director",
    "architect",
    "administrator",
    "qa",
    "tester",
}
COMPANY_MARKERS = {"inc", "llc", "ltd", "corp", "company", "gmbh", "plc"}


class ExperienceParser:
    def parse(self, blocks: list[TextBlock]) -> list[ExperienceEntry]:
        lines = [block.text for block in blocks if block.text.strip()]
        if not lines:
            return []

        entries = [self._parse_entry(group) for group in self._split_entries(lines)]
        return [entry for entry in entries if entry.raw_text]

    def _split_entries(self, lines: list[str]) -> list[list[str]]:
        entries: list[list[str]] = []
        current: list[str] = []

        for line in lines:
            if current and self._starts_new_entry(line, current):
                entries.append(current)
                current = [line]
                continue
            current.append(line)

        if current:
            entries.append(current)

        return entries

    def _starts_new_entry(self, line: str, current: list[str]) -> bool:
        if extract_date_range(line) and (
            any(extract_date_range(existing) for existing in current)
            or any(existing.startswith("- ") for existing in current)
            or len(current) >= 3
        ):
            return True

        if (
            len(line.split()) <= 8
            and not line.startswith("- ")
            and not extract_date_range(line)
            and any(existing.startswith("- ") for existing in current)
        ):
            return True

        return False

    def _parse_entry(self, lines: list[str]) -> ExperienceEntry:
        raw_text = "\n".join(lines).strip()
        header_lines = [line for line in lines[:3] if not line.startswith("- ")]
        date_range_raw = next((extract_date_range(line) for line in lines if extract_date_range(line)), None)
        start_date, end_date = split_date_range(date_range_raw)

        title, company, location = self._classify_header_lines(header_lines)
        bullets = [line.removeprefix("- ").strip() for line in lines if line.startswith("- ")]
        description_lines = [
            line
            for line in lines
            if line not in header_lines and not line.startswith("- ")
        ]
        description_raw = "\n".join(description_lines).strip() or None

        return ExperienceEntry(
            title=title,
            company=company,
            start_date=start_date,
            end_date=end_date,
            date_range_raw=date_range_raw,
            location=location,
            bullets=bullets,
            description_raw=description_raw,
            raw_text=raw_text or None,
        )

    def _classify_header_lines(
        self,
        header_lines: list[str],
    ) -> tuple[str | None, str | None, str | None]:
        cleaned = [self._remove_date_text(line) for line in header_lines if self._remove_date_text(line)]
        if not cleaned:
            return None, None, None

        if len(cleaned) == 1:
            return self._split_combined_header(cleaned[0])

        title = self._prefer_title(cleaned[0], cleaned[1])
        company = cleaned[1] if title == cleaned[0] else cleaned[0]
        location = next(
            (
                line
                for line in cleaned[2:]
                if "," in line and not any(char.isdigit() for char in line)
            ),
            None,
        )
        return title, company, location

    def _split_combined_header(self, line: str) -> tuple[str | None, str | None, str | None]:
        for separator in (" at ", " @ ", " | ", " - "):
            if separator in line.lower():
                parts = re.split(re.escape(separator), line, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    return parts[0].strip() or None, parts[1].strip() or None, None

        lowered = line.lower()
        if any(marker in lowered for marker in COMPANY_MARKERS):
            return None, line, None
        if any(keyword in lowered for keyword in ROLE_KEYWORDS):
            return line, None, None
        return line, None, None

    def _prefer_title(self, first: str, second: str) -> str:
        first_score = sum(keyword in first.lower() for keyword in ROLE_KEYWORDS)
        second_score = sum(keyword in second.lower() for keyword in ROLE_KEYWORDS)
        return first if first_score >= second_score else second

    def _remove_date_text(self, line: str) -> str:
        date_range = extract_date_range(line)
        if not date_range:
            return line.strip()
        return line.replace(date_range, "").strip(" |,-")
