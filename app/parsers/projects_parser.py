from app.parsers.generic_list_parser import GenericListParser
from app.schemas.content import GenericListSection, TextBlock


class ProjectsParser:
    def __init__(self) -> None:
        self._list_parser = GenericListParser()

    def parse(self, blocks: list[TextBlock]) -> GenericListSection:
        return self._list_parser.parse(
            blocks,
            split_only_if_list_like=False,
            split_on_date_boundaries=True,
            max_item_length=260,
        )
