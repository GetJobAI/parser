from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.content import SectionMatch, TextBlock


class SectionedDocument(BaseModel):
    header_blocks: list[TextBlock] = Field(default_factory=list)
    sections: dict[str, list[TextBlock]] = Field(default_factory=dict)
    unassigned_blocks: list[TextBlock] = Field(default_factory=list)


def build_section_map(
    blocks: list[TextBlock],
    matches: list[SectionMatch],
) -> SectionedDocument:
    if not matches:
        return SectionedDocument(
            header_blocks=blocks[:6],
            sections={},
            unassigned_blocks=blocks[6:],
        )

    order_to_index = {block.order: index for index, block in enumerate(blocks)}
    sorted_matches = sorted(matches, key=lambda match: match.block_order)
    first_match_index = order_to_index.get(sorted_matches[0].block_order, 0)

    sections: dict[str, list[TextBlock]] = {}

    for index, match in enumerate(sorted_matches):
        start = order_to_index.get(match.block_order, 0) + 1
        end = (
            order_to_index.get(sorted_matches[index + 1].block_order, len(blocks))
            if index + 1 < len(sorted_matches)
            else len(blocks)
        )
        sections.setdefault(match.canonical_name, []).extend(blocks[start:end])

    return SectionedDocument(
        header_blocks=blocks[:first_match_index],
        sections=sections,
        unassigned_blocks=[],
    )
