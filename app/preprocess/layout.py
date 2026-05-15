from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel

from app.schemas.content import TextBlock


class LayoutResult(BaseModel):
    blocks: list[TextBlock]
    layout_detected: str


def detect_layout_and_reorder(blocks: list[TextBlock]) -> LayoutResult:
    if not blocks or all(block.page is None or block.x0 is None for block in blocks):
        return LayoutResult(blocks=blocks, layout_detected="single_column")

    pages: dict[int, list[TextBlock]] = defaultdict(list)
    for block in blocks:
        pages[block.page or 0].append(block)

    ordered: list[TextBlock] = []
    any_two_column = False

    for page_number in sorted(pages):
        page_blocks = pages[page_number]
        if _is_two_column(page_blocks):
            any_two_column = True
            mids = [(block.x0 + block.x1) / 2 for block in page_blocks if block.x0 is not None and block.x1 is not None]
            split_x = sum(mids) / len(mids) if mids else 0.0
            left = [block for block in page_blocks if ((block.x0 or 0.0) + (block.x1 or 0.0)) / 2 <= split_x]
            right = [block for block in page_blocks if ((block.x0 or 0.0) + (block.x1 or 0.0)) / 2 > split_x]
            ordered.extend(sorted(left, key=_position_key))
            ordered.extend(sorted(right, key=_position_key))
        else:
            ordered.extend(sorted(page_blocks, key=_position_key))

    for order, block in enumerate(ordered):
        block.order = order

    return LayoutResult(
        blocks=ordered,
        layout_detected="two_column" if any_two_column else "single_column",
    )


def _is_two_column(blocks: list[TextBlock]) -> bool:
    coordinate_blocks = [block for block in blocks if block.x0 is not None and block.x1 is not None]
    if len(coordinate_blocks) < 6:
        return False

    x0_values = sorted(block.x0 for block in coordinate_blocks if block.x0 is not None)
    if not x0_values:
        return False
    if max(x0_values) - min(x0_values) < 80:
        return False

    centers = sorted(((block.x0 + block.x1) / 2) for block in coordinate_blocks)
    split_x = sum(centers) / len(centers)
    left = [center for center in centers if center < split_x - 20]
    right = [center for center in centers if center > split_x + 20]
    if len(left) < 2 or len(right) < 2:
        return False

    return (len(left) / len(centers)) >= 0.25 and (len(right) / len(centers)) >= 0.25


def _position_key(block: TextBlock) -> tuple[float, float]:
    return (
        float("inf") if block.y0 is None else block.y0,
        float("inf") if block.x0 is None else block.x0,
    )
