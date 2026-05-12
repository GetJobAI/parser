from app.parsers.generic_list_parser import GenericListParser
from app.schemas.content import GenericListSection, TextBlock


class LanguagesParser:
    def __init__(self) -> None:
        self._list_parser = GenericListParser()

    def parse(self, blocks: list[TextBlock]) -> GenericListSection:
        return self._list_parser.parse(
            blocks,
            split_only_if_list_like=True,
            split_on_middot=True,
            max_item_length=120,
        )
