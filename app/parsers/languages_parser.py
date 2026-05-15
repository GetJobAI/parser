from app.parsers.generic_list_parser import GenericListParser
from app.schemas.content import LanguageEntry, TextBlock


class LanguagesParser:
    def __init__(self) -> None:
        self._list_parser = GenericListParser()

    def parse(self, blocks: list[TextBlock]) -> list[LanguageEntry]:
        items = self._list_parser.parse_items(
            blocks,
            split_only_if_list_like=True,
            split_on_middot=True,
            max_item_length=120,
        )
        entries: list[LanguageEntry] = []
        for item in items:
            if "—" in item:
                name, level = [part.strip() for part in item.split("—", maxsplit=1)]
            elif "-" in item:
                name, level = [part.strip() for part in item.split("-", maxsplit=1)]
            else:
                name, level = item.strip(), None
            if name:
                entries.append(LanguageEntry(name=name, level=level or None))
        return entries
