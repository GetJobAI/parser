from app.parsers.contact_parser import ContactParser
from app.schemas.content import TextBlock


def test_contact_parser_extracts_location_from_mixed_contact_line_without_fake_website() -> None:
    parser = ContactParser()
    blocks = [
        TextBlock(text="Mykhailo Savchenko", order=0),
        TextBlock(
            text="Wrocław, Poland · m.savchenko@stolarz.pl · +48 512 384 921 · linkedin.com/in/msavchenko-stolarz",
            order=1,
        ),
    ]

    contact = parser.parse(blocks)

    assert contact.name == "Mykhailo Savchenko"
    assert contact.location == "Wrocław, Poland"
    assert contact.linkedin == "linkedin.com/in/msavchenko-stolarz"
