"""Integration tests for the validation engine against bundled schemas."""

import os

from moph_report import loader
from moph_report.schema import load_schema, list_schemas
from moph_report.validator import validate

EXAMPLES = os.path.join(os.path.dirname(__file__), os.pardir, "examples")


def test_bundled_schemas_present():
    names = list_schemas()
    assert "PERSON" in names
    assert "SERVICE" in names
    assert "DIAGNOSIS_OPD" in names
    assert "DEATH" in names


def test_clean_person_file_passes():
    schema = load_schema("PERSON")
    data = loader.load(os.path.join(EXAMPLES, "person_sample.txt"))
    result = validate(data, schema)
    assert result.total_rows == 3
    assert result.is_valid, [i.message for i in result.errors]
    assert result.errors == []


def test_dirty_person_file_catches_errors():
    schema = load_schema("PERSON")
    data = loader.load(os.path.join(EXAMPLES, "person_with_errors.txt"))
    result = validate(data, schema)
    assert not result.is_valid

    rules_hit = {i.rule for i in result.errors}
    # Bad national-ID check digit on row 2.
    assert "cid_checksum" in rules_hit
    # Buddhist-era birth date on row 2.
    assert "date_buddhist_era" in rules_hit
    # SEX=3 and TYPEAREA=7 are outside their allowed code sets.
    assert "allowed_values" in rules_hit
    # Missing required D_UPDATE on row 3.
    assert "required" in rules_hit
    # Row 4 duplicates row 1's (HOSPCODE, CID) primary key.
    assert "duplicate_key" in rules_hit


def test_missing_required_column_is_error():
    schema = load_schema("PERSON")
    # A file missing the required CID column.
    data = loader.DataFile(
        header=["HOSPCODE", "PID"],
        rows=[["11111", "P1"]],
        delimiter="|",
        encoding="utf-8",
    )
    result = validate(data, schema)
    missing = [i for i in result.errors if i.rule == "missing_column"]
    assert any(i.column == "CID" for i in missing)
