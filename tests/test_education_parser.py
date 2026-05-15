from app.parsers.education_parser import EducationParser
from app.schemas.content import TextBlock


def test_education_parser_extracts_degree_and_location_from_single_line() -> None:
    parser = EducationParser()
    blocks = [
        TextBlock(
            text="Centrum Kształcenia Zawodowego nr 1 09.2012 – 06.2014 Vocational Certificate — Stolarz (Carpenter) Wrocław, Poland",
            order=0,
        ),
        TextBlock(text="Grade: Celujący (6/6)", order=1),
    ]

    entries = parser.parse(blocks)

    assert len(entries) == 1
    assert entries[0].institution == "Centrum Kształcenia Zawodowego nr 1"
    assert entries[0].degree == "Vocational Certificate — Stolarz (Carpenter)"
    assert entries[0].location == "Wrocław, Poland"
    assert entries[0].grade == "Celujący (6/6)"
