from __future__ import annotations

import re

from app.schemas.content import GenericListSection, TextBlock
from app.utils.text import blocks_to_text

LIST_SEPARATOR_RE = re.compile(r"\s*(?:\n|,|;|\||•)\s*")
DATE_BOUNDARY_RE = re.compile(r"((?:\d{1,2}[./-]\d{4}|\d{4})\.?)\s+(?=[A-ZА-Я])")


class GenericListParser:
    def parse(
        self,
        blocks: list[TextBlock],
        *,
        split_only_if_list_like: bool = False,
        split_on_middot: bool = False,
        split_on_date_boundaries: bool = False,
        max_item_length: int = 220,
    ) -> GenericListSection:
        raw_text = blocks_to_text(blocks) or None
        if not raw_text:
            return GenericListSection()

        items = self._extract_items(
            raw_text,
            split_only_if_list_like=split_only_if_list_like,
            split_on_middot=split_on_middot,
            split_on_date_boundaries=split_on_date_boundaries,
            max_item_length=max_item_length,
        )
        return GenericListSection(items=items, raw_text=raw_text)

    def _extract_items(
        self,
        text: str,
        *,
        split_only_if_list_like: bool,
        split_on_middot: bool,
        split_on_date_boundaries: bool,
        max_item_length: int,
    ) -> list[str]:
        list_like = (
            "\n- " in text
            or text.count(",") >= 2
            or text.count("|") >= 1
            or text.count(";") >= 1
            or text.count("•") >= 1
            or (split_on_middot and text.count("·") >= 1)
        )
        if split_only_if_list_like and not list_like:
            return []

        split_text = text
        if split_on_middot:
            split_text = split_text.replace(" · ", "\n")

        raw_items = [item.strip(" -") for item in LIST_SEPARATOR_RE.split(split_text) if item.strip(" -")]
        if split_on_date_boundaries and len(text) > 40:
            split_by_dates = DATE_BOUNDARY_RE.sub(r"\1\n", text)
            raw_items = [item.strip(" -") for item in split_by_dates.splitlines() if item.strip(" -")]
        elif len(raw_items) <= 1 and len(text) > 120:
            split_by_dates = DATE_BOUNDARY_RE.sub(r"\1\n", text)
            raw_items = [item.strip(" -") for item in split_by_dates.splitlines() if item.strip(" -")]

        unique_items = list(dict.fromkeys(item for item in raw_items if len(item) <= max_item_length))
        return unique_items
