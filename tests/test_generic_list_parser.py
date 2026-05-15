from app.parsers.generic_list_parser import GenericListParser
from app.schemas.content import TextBlock


def test_generic_list_parser_splits_middot_languages() -> None:
    parser = GenericListParser()
    items = parser.parse_items(
        [
            TextBlock(
                text="Ukrainian — Native · Polish — Fluent (C1) · Russian — Professional Working (C1) · English — Elementary (A2)",
                order=0,
            )
        ],
        split_on_middot=True,
    )

    assert items == [
        "Ukrainian — Native",
        "Polish — Fluent (C1)",
        "Russian — Professional Working (C1)",
        "English — Elementary (A2)",
    ]
