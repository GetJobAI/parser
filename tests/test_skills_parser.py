from app.parsers.skills_parser import SkillsParser
from app.schemas.content import TextBlock


def test_skills_parser_preserves_category_context() -> None:
    parser = SkillsParser()
    section = parser.parse(
        [
            TextBlock(
                text=(
                    "Joinery: Mortise & tenon, Dovetail, Finger joint "
                    "Machines: CNC router, Panel saw "
                    "Finishing: Oil & wax, Water-based lacquer "
                    "Software: SketchUp, AutoCAD LT"
                ),
                order=0,
            )
        ]
    )

    assert [(group.category, group.items) for group in section] == [
        ("Joinery", ["Mortise & tenon", "Dovetail", "Finger joint"]),
        ("Machines", ["CNC router", "Panel saw"]),
        ("Finishing", ["Oil & wax", "Water-based lacquer"]),
        ("Software", ["SketchUp", "AutoCAD LT"]),
    ]
