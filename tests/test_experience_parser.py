from app.parsers.experience_parser import ExperienceParser
from app.schemas.content import TextBlock


def test_experience_parser_keeps_partial_but_honest_structure() -> None:
    parser = ExperienceParser()
    blocks = [
        TextBlock(text="Senior Backend Engineer", order=0),
        TextBlock(text="Acme Corp", order=1),
        TextBlock(text="Jan 2020 - Present", order=2),
        TextBlock(text="- Built parsing APIs", order=3),
        TextBlock(text="- Reduced latency", order=4),
    ]

    entries = parser.parse(blocks)

    assert len(entries) == 1
    assert entries[0].title == "Senior Backend Engineer"
    assert entries[0].company == "Acme Corp"
    assert entries[0].start_date == "Jan 2020"
    assert entries[0].end_date == "Present"
    assert entries[0].bullets == ["Built parsing APIs", "Reduced latency"]


def test_experience_parser_keeps_leading_description_outside_header() -> None:
    parser = ExperienceParser()
    blocks = [
        TextBlock(text="Drewno & Forma 03.2018 – present Master Carpenter Wrocław, Poland", order=0),
        TextBlock(
            text="Design and build bespoke solid oak and walnut furniture to client specifications.",
            order=1,
        ),
        TextBlock(text="- Operate CNC router and edge bander for precision panel work.", order=2),
    ]

    entries = parser.parse(blocks)

    assert len(entries) == 1
    assert entries[0].company == "Drewno & Forma"
    assert entries[0].title == "Master Carpenter"
    assert entries[0].location == "Wrocław, Poland"
    assert entries[0].description_raw == (
        "Design and build bespoke solid oak and walnut furniture to client specifications."
    )
