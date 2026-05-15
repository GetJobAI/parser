from app.parsers.generic_list_parser import GenericListParser
from app.schemas.content import CertificationEntry, TextBlock


def _split_certification(item: str) -> CertificationEntry:
    parts = [part.strip() for part in item.split("·")]
    left = parts[0] if parts else item.strip()
    right = parts[1] if len(parts) > 1 else ""
    issuer, date = right, None
    if right:
        tokens = right.rsplit(" ", maxsplit=1)
        if len(tokens) == 2 and any(char.isdigit() for char in tokens[1]):
            issuer, date = tokens[0].strip(), tokens[1].strip()
    return CertificationEntry(name=left or None, issuer=issuer or None, date=date or None)


class CertificationsParser:
    def __init__(self) -> None:
        self._list_parser = GenericListParser()

    def parse(self, blocks: list[TextBlock]) -> list[CertificationEntry]:
        items = self._list_parser.parse_items(
            blocks,
            split_only_if_list_like=False,
            split_on_date_boundaries=True,
            max_item_length=180,
        )
        return [_split_certification(item) for item in items]
