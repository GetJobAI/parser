from __future__ import annotations

import re

from app.schemas.content import GenericListSection, TextBlock
from app.utils.text import blocks_to_text

LIST_SEPARATOR_RE = re.compile(r"\s*(?:\n|,|;|\||•)\s*")


class GenericListParser:
    def parse(
        self,
        blocks: list[TextBlock],
        *,
        split_only_if_list_like: bool = False,
    ) -> GenericListSection:
        raw_text = blocks_to_text(blocks) or None
        if not raw_text:
            return GenericListSection()

        items = self._extract_items(raw_text, split_only_if_list_like=split_only_if_list_like)
        return GenericListSection(items=items, raw_text=raw_text)

    def _extract_items(self, text: str, *, split_only_if_list_like: bool) -> list[str]:
        list_like = (
            "\n- " in text
            or text.count(",") >= 2
            or text.count("|") >= 1
            or text.count(";") >= 1
            or text.count("•") >= 1
        )
        if split_only_if_list_like and not list_like:
            return []

        raw_items = [item.strip(" -") for item in LIST_SEPARATOR_RE.split(text) if item.strip(" -")]
        unique_items = list(dict.fromkeys(item for item in raw_items if len(item) <= 120))
        return unique_items
