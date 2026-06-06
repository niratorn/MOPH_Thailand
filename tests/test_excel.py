"""Tests for Excel report output (skipped if openpyxl is not installed)."""

import os

import pytest

from moph_report import loader, report
from moph_report.schema import load_schema
from moph_report.validator import validate

openpyxl = pytest.importorskip("openpyxl")

EXAMPLES = os.path.join(os.path.dirname(__file__), os.pardir, "examples")


def test_write_issues_xlsx(tmp_path):
    schema = load_schema("PERSON")
    data = loader.load(os.path.join(EXAMPLES, "person_with_errors.txt"))
    result = validate(data, schema)

    out = tmp_path / "report.xlsx"
    report.write_issues_xlsx(result, str(out))
    assert out.exists()

    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Summary", "Issues"]
    # Header row + one row per issue.
    assert wb["Issues"].max_row == len(result.issues) + 1
