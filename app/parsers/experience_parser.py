from __future__ import annotations

import re

from app.schemas.content import ExperienceEntry, TextBlock
from app.utils.regexes import extract_date_range, split_date_range

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
    "assistant",
    "carpenter",
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
        header_lines = self._extract_header_lines(lines)
        date_range_raw = next((extract_date_range(line) for line in lines if extract_date_range(line)), None)
        start_date, end_date = split_date_range(date_range_raw)
        title, company, location, header_description = self._classify_header_lines(
            header_lines, date_range_raw=date_range_raw
        )
        bullets = [line.removeprefix("- ").strip() for line in lines if line.startswith("- ")]
        description_lines = header_description + [
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

    def _extract_header_lines(self, lines: list[str]) -> list[str]:
        non_bullet_lines = [line for line in lines if not line.startswith("- ")]
        if not non_bullet_lines:
            return []

        if extract_date_range(non_bullet_lines[0]):
            return [non_bullet_lines[0]]

        if len(non_bullet_lines) >= 2 and extract_date_range(non_bullet_lines[1]):
            return non_bullet_lines[:2]

        header_lines = [non_bullet_lines[0]]
        if len(non_bullet_lines) >= 2 and self._looks_like_header_line(non_bullet_lines[1]):
            header_lines.append(non_bullet_lines[1])
        return header_lines

    def _classify_header_lines(
        self,
        header_lines: list[str],
        *,
        date_range_raw: str | None,
    ) -> tuple[str | None, str | None, str | None, list[str]]:
        cleaned = [self._remove_date_text(line) for line in header_lines if self._remove_date_text(line)]
        if not cleaned:
            return None, None, None, []

        if len(header_lines) >= 2 and extract_date_range(header_lines[1]):
            inferred = self._extract_title_company_location_from_dated_line(
                header_lines[1], date_range_raw, company_hint=cleaned[0]
            )
            if inferred is not None:
                return inferred

        if header_lines and extract_date_range(header_lines[0]):
            inferred = self._extract_title_company_location_from_dated_line(header_lines[0], date_range_raw)
            if inferred is not None:
                return inferred

        if len(cleaned) == 1:
            title, company, location = self._split_combined_header(cleaned[0])
            return title, company, location, []

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
        return title, company, location, []

    def _extract_title_company_location_from_dated_line(
        self,
        raw_line: str,
        date_range_raw: str | None,
        *,
        company_hint: str | None = None,
    ) -> tuple[str | None, str | None, str | None, list[str]] | None:
        if not date_range_raw or date_range_raw not in raw_line:
            return None

        left, right = raw_line.split(date_range_raw, maxsplit=1)
        company = left.strip(" |,-") or company_hint
        right_text = right.strip(" |,-")
        if not right_text:
            return None

        title, location, remainder = self._split_title_location_description(right_text)
        description_lines = [remainder] if remainder else []
        return title, company, location, description_lines

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

    def _looks_like_header_line(self, line: str) -> bool:
        lowered = line.lower()
        return (
            extract_date_range(line) is not None
            or len(line.split()) <= 10
            or any(keyword in lowered for keyword in ROLE_KEYWORDS)
            or any(marker in lowered for marker in COMPANY_MARKERS)
        )

    def _split_title_location_description(self, text: str) -> tuple[str | None, str | None, str | None]:
        if "," in text:
            before_comma, after_comma = text.split(",", maxsplit=1)
            after_tokens = after_comma.strip().split(maxsplit=1)
            country = after_tokens[0] if after_tokens else ""
            rest = after_tokens[1].strip() if len(after_tokens) > 1 else None
            before_tokens = before_comma.strip().split()

            best_candidate: tuple[str, str] | None = None
            best_score = -1
            max_city_tokens = min(3, max(1, len(before_tokens) - 1))
            for city_len in range(1, max_city_tokens + 1):
                title_tokens = before_tokens[:-city_len]
                city_tokens = before_tokens[-city_len:]
                if not title_tokens or not city_tokens:
                    continue

                title_candidate = " ".join(title_tokens).strip()
                city_candidate = " ".join(city_tokens).strip()
                if any(keyword in city_candidate.lower() for keyword in ROLE_KEYWORDS):
                    continue

                score = sum(keyword in title_candidate.lower() for keyword in ROLE_KEYWORDS)
                if "—" in title_candidate or "-" in title_candidate:
                    score += 1

                if score > best_score:
                    best_score = score
                    best_candidate = (title_candidate, city_candidate)

            if best_candidate is not None and country:
                title_candidate, city_candidate = best_candidate
                return title_candidate or None, f"{city_candidate}, {country}", rest

            if before_comma.strip() and after_comma.strip():
                return before_comma.strip(), after_comma.strip(), None

        return text.strip() or None, None, None

    def _remove_date_text(self, line: str) -> str:
        date_range = extract_date_range(line)
        if not date_range:
            return line.strip()
        return line.replace(date_range, "").strip(" |,-")
