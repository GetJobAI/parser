from app.schemas.content import SummarySection, TextBlock
from app.utils.text import blocks_to_text


class SummaryParser:
    def parse(self, blocks: list[TextBlock]) -> SummarySection:
        return SummarySection(raw_text=blocks_to_text(blocks) or None)
