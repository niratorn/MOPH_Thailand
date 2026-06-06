"""Tests for cross-file referential integrity checks."""

import os

from moph_report import crosscheck, loader

EXAMPLES = os.path.join(os.path.dirname(__file__), os.pardir, "examples")


def _load(name):
    return loader.load(os.path.join(EXAMPLES, name))


def test_service_references_person_ok():
    files = {
        "PERSON": _load("person_sample.txt"),
        "SERVICE": _load("service_sample.txt"),
    }
    result = crosscheck.crosscheck(files)
    assert "SERVICE.PID -> PERSON.PID" in result.checked
    assert result.is_valid, [i.message for i in result.issues]


def test_diagnosis_orphan_is_detected():
    files = {
        "PERSON": _load("person_sample.txt"),
        "SERVICE": _load("service_sample.txt"),
        "DIAGNOSIS_OPD": _load("diagnosis_opd_sample.txt"),
    }
    result = crosscheck.crosscheck(files)
    assert not result.is_valid
    # The P0009/68009999 diagnosis row has no matching SERVICE visit.
    orphans = [i for i in result.issues if i.child == "DIAGNOSIS_OPD"]
    assert len(orphans) == 1
    assert "P0009|68009999" in orphans[0].key


def test_relationship_skipped_when_parent_absent():
    # Only the child file is supplied -> relationship cannot be evaluated.
    files = {"DIAGNOSIS_OPD": _load("diagnosis_opd_sample.txt")}
    result = crosscheck.crosscheck(files)
    assert result.checked == []
    assert result.is_valid  # nothing to check means no orphans
