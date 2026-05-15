from app.schemas.content import TextBlock
from app.utils.text import blocks_to_text


class SummaryParser:
    def parse(self, blocks: list[TextBlock]) -> str | None:
        return blocks_to_text(blocks) or None
