from __future__ import annotations

import re

from app.parsers.generic_list_parser import GenericListParser
from app.schemas.content import SkillGroup, TextBlock
from app.utils.text import blocks_to_text

SKILL_CATEGORY_RE = re.compile(r"(?:^|\s)([A-Z][A-Za-z&/+.-]*(?:\s+[A-Z][A-Za-z&/+.-]*){0,2}):")
SKILL_ITEM_RE = re.compile(r"\s*(?:,|;|\||•)\s*")
CATEGORY_SUFFIXES = {
    "Languages",
    "Infrastructure",
    "Concepts",
    "Software",
    "Machines",
    "Finishing",
    "Joinery",
    "Tools",
    "Frameworks",
    "Platforms",
    "Databases",
}


class SkillsParser:
    def __init__(self) -> None:
        self._list_parser = GenericListParser()

    def parse(self, blocks: list[TextBlock]) -> list[SkillGroup]:
        raw_text = blocks_to_text(blocks) or None
        if not raw_text:
            return []

        grouped = self._extract_category_items(raw_text)
        if grouped:
            return grouped

        items = self._list_parser.parse_items(blocks, split_only_if_list_like=True)
        if not items:
            return []
        return [SkillGroup(category="General", items=items)]

    def _extract_category_items(self, text: str) -> list[SkillGroup]:
        matches = list(SKILL_CATEGORY_RE.finditer(text))
        if not matches:
            return []

        groups: list[SkillGroup] = []
        for index, match in enumerate(matches):
            raw_category = match.group(1).strip()
            category = raw_category.title()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            category = self._normalize_category(category, raw_category, groups)
            segment = text[start:end].strip(" -")
            if not segment:
                continue

            items: list[str] = []
            for part in SKILL_ITEM_RE.split(segment):
                cleaned = part.strip(" -")
                if not cleaned:
                    continue
                items.append(cleaned)

            groups.append(SkillGroup(category=category, items=list(dict.fromkeys(items))))

        return groups

    def _normalize_category(self, category: str, raw_category: str, groups: list[SkillGroup]) -> str:
        words = category.split()
        raw_words = raw_category.split()
        if len(words) <= 1:
            return category
        suffix = words[-1]
        prefix = " ".join(raw_words[:-1]).strip()
        if suffix in CATEGORY_SUFFIXES and prefix and groups:
            groups[-1].items.append(prefix)
            groups[-1].items = list(dict.fromkeys(groups[-1].items))
            return suffix
        return category
