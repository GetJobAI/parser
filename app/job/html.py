from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html import unescape
from typing import Any

from app.utils.text import collapse_whitespace, compact_lines

SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript|svg|canvas|iframe|form)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
LD_JSON_RE = re.compile(
    r"<script\b[^>]*type=(['\"])application/ld\+json\1[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_RE = re.compile(r"<meta\b([^>]+)>", re.IGNORECASE)
ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(".*?"|\'.*?\'|[^\s>]+)')
TAG_RE = re.compile(r"<[^>]+>")
SALARY_RE = re.compile(
    r"(?:(?:USD|EUR|GBP|PLN|UAH|CAD|AUD|CHF)\s*)?"
    r"(?:\$|€|£)?\s?\d[\d\s,.]*(?:k|K)?\s*(?:-|–|to)\s*(?:\$|€|£)?\s?\d[\d\s,.]*(?:k|K)?"
    r"(?:\s*/\s*(?:year|yr|month|mo|hour|hr))?",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ExtractedJobDocument:
    text: str
    title_candidates: list[str] = field(default_factory=list)
    meta_title: str | None = None
    meta_description: str | None = None
    structured_data: dict[str, Any] | None = None
    salary_hint: str | None = None
    warnings: list[str] = field(default_factory=list)


class HTMLJobExtractor:
    def extract(self, html: str) -> ExtractedJobDocument:
        structured_data = self._extract_job_posting_ld_json(html)
        title_candidates = self._extract_title_candidates(html)
        meta_title, meta_description = self._extract_meta_tags(html)
        text = self._html_to_text(html)
        salary_hint = self._extract_salary_hint(text)
        warnings: list[str] = []
        if len(text) < 120:
            warnings.append("Very little readable job posting text was extracted from HTML.")
        return ExtractedJobDocument(
            text=text,
            title_candidates=title_candidates,
            meta_title=meta_title,
            meta_description=meta_description,
            structured_data=structured_data,
            salary_hint=salary_hint,
            warnings=warnings,
        )

    def _extract_job_posting_ld_json(self, html: str) -> dict[str, Any] | None:
        for _, raw_payload in LD_JSON_RE.findall(html):
            payload = unescape(raw_payload).strip()
            if not payload:
                continue
            try:
                decoded = json.loads(payload)
            except json.JSONDecodeError:
                continue
            job_posting = self._find_job_posting_object(decoded)
            if job_posting:
                return job_posting
        return None

    def _find_job_posting_object(self, value: Any) -> dict[str, Any] | None:
        if isinstance(value, list):
            for item in value:
                found = self._find_job_posting_object(item)
                if found:
                    return found
            return None
        if not isinstance(value, dict):
            return None

        raw_type = value.get("@type") or value.get("type")
        if isinstance(raw_type, list):
            types = {str(item).lower() for item in raw_type}
        else:
            types = {str(raw_type).lower()} if raw_type else set()
        if "jobposting" in types:
            return value

        for nested_value in value.values():
            found = self._find_job_posting_object(nested_value)
            if found:
                return found
        return None

    def _extract_title_candidates(self, html: str) -> list[str]:
        candidates: list[str] = []
        for match in H1_RE.findall(html):
            cleaned = self._clean_inline_html(match)
            if cleaned:
                candidates.append(cleaned)
        title_match = TITLE_RE.search(html)
        if title_match:
            cleaned = self._clean_inline_html(title_match.group(1))
            if cleaned:
                candidates.append(cleaned)
        return list(dict.fromkeys(candidates))

    def _extract_meta_tags(self, html: str) -> tuple[str | None, str | None]:
        meta_title: str | None = None
        meta_description: str | None = None
        for raw_attrs in META_RE.findall(html):
            attrs = {
                key.lower(): value.strip("\"'")
                for key, value in ATTR_RE.findall(raw_attrs)
            }
            content = collapse_whitespace(unescape(attrs.get("content", "")))
            if not content:
                continue
            name = attrs.get("name", "").lower()
            prop = attrs.get("property", "").lower()
            if name == "description" and not meta_description:
                meta_description = content
            if prop in {"og:title", "twitter:title"} and not meta_title:
                meta_title = content
            if prop in {"og:description", "twitter:description"} and not meta_description:
                meta_description = content
        return meta_title, meta_description

    def _html_to_text(self, html: str) -> str:
        cleaned = COMMENT_RE.sub(" ", html)
        cleaned = SCRIPT_STYLE_RE.sub(" ", cleaned)
        cleaned = re.sub(r"(?i)<br\s*/?>", "\n", cleaned)
        cleaned = re.sub(r"(?i)<li\b[^>]*>", "\n- ", cleaned)
        cleaned = re.sub(r"(?i)</(li|p|div|section|article|main|aside|header|footer|h1|h2|h3|h4|h5|h6|ul|ol|table|tr)>", "\n", cleaned)
        cleaned = TAG_RE.sub(" ", cleaned)
        cleaned = unescape(cleaned)
        cleaned = cleaned.replace("\xa0", " ")
        lines = compact_lines(line for line in cleaned.splitlines())
        return "\n".join(lines).strip()

    def _clean_inline_html(self, value: str) -> str:
        return collapse_whitespace(unescape(TAG_RE.sub(" ", value)))

    def _extract_salary_hint(self, text: str) -> str | None:
        match = SALARY_RE.search(text)
        if not match:
            return None
        return collapse_whitespace(match.group(0))
