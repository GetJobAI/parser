from __future__ import annotations

import re

from app.parsers.generic_list_parser import GenericListParser
from app.schemas.content import GenericListSection, TextBlock
from app.utils.text import blocks_to_text

SKILL_CATEGORY_RE = re.compile(r"(Joinery|Machines|Finishing|Software):", re.IGNORECASE)
SKILL_ITEM_RE = re.compile(r"\s*(?:,|;|\||•)\s*")


class SkillsParser:
    def __init__(self) -> None:
        self._list_parser = GenericListParser()

    def parse(self, blocks: list[TextBlock]) -> GenericListSection:
        raw_text = blocks_to_text(blocks) or None
        if not raw_text:
            return GenericListSection()

        category_items = self._extract_category_items(raw_text)
        if category_items:
            return GenericListSection(items=category_items, raw_text=raw_text)

        return self._list_parser.parse(blocks, split_only_if_list_like=True)

    def _extract_category_items(self, text: str) -> list[str]:
        matches = list(SKILL_CATEGORY_RE.finditer(text))
        if not matches:
            return []

        items: list[str] = []
        for index, match in enumerate(matches):
            category = match.group(1).strip().title()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            segment = text[start:end].strip(" -")
            if not segment:
                continue

            for part in SKILL_ITEM_RE.split(segment):
                cleaned = part.strip(" -")
                if not cleaned:
                    continue
                items.append(f"{category}: {cleaned}")

        return list(dict.fromkeys(items))
