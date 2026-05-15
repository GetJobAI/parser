from app.parsers.certifications_parser import CertificationsParser
from app.schemas.content import TextBlock


def test_certifications_parser_splits_entries_by_date_boundary() -> None:
    parser = CertificationsParser()
    section = parser.parse(
        [
            TextBlock(
                text=(
                    "Uprawnienia do obsługi CNC — klasa I · Instytut Mechanizacji Budownictwa 03.2016 "
                    "Karta Polaka · Rzeczpospolita Polska 11.2010"
                ),
                order=0,
            )
        ]
    )

    assert [(entry.name, entry.issuer, entry.date) for entry in section] == [
        ("Uprawnienia do obsługi CNC — klasa I", "Instytut Mechanizacji Budownictwa", "03.2016"),
        ("Karta Polaka", "Rzeczpospolita Polska", "11.2010"),
    ]
