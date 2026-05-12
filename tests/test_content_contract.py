from app.schemas.contract import build_resume_content_contract


def test_resume_content_contract_exposes_core_sections() -> None:
    contract = build_resume_content_contract()

    schema_properties = contract.content_schema["properties"]
    assert "meta" in schema_properties
    assert "contact" in schema_properties
    assert "summary" in schema_properties
    assert "experience" in schema_properties
    assert "education" in schema_properties
    assert "skills" in schema_properties
    assert "unassigned_blocks" in schema_properties

    example = contract.content_example
    assert example["summary"]["raw_text"] is not None
    assert "items" in example["skills"]
    assert "meta" in example
