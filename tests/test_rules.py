"""Unit tests for the low-level validation rules."""

from moph_report import rules


def test_valid_thai_cid():
    # These all carry a correct check digit.
    assert rules.is_valid_thai_cid("1101700203450")
    assert rules.is_valid_thai_cid("1101700203468")
    assert rules.is_valid_thai_cid("1101700203476")


def test_invalid_thai_cid():
    assert not rules.is_valid_thai_cid("1101700203451")  # bad check digit
    assert not rules.is_valid_thai_cid("123")            # too short
    assert not rules.is_valid_thai_cid("abcdefghijklm")  # not digits
    assert not rules.is_valid_thai_cid("")


def test_date_yyyymmdd():
    assert rules.is_valid_date_yyyymmdd("19800115")
    assert rules.is_valid_date_yyyymmdd("20260606")
    assert not rules.is_valid_date_yyyymmdd("2026-06-06")
    assert not rules.is_valid_date_yyyymmdd("20260230")  # Feb 30 not real
    assert not rules.is_valid_date_yyyymmdd("19801332")  # bad month/day


def test_buddhist_era_detection():
    assert rules.is_buddhist_era_year("25350320")  # พ.ศ. 2535
    assert not rules.is_buddhist_era_year("19920320")


def test_datetime():
    assert rules.is_valid_datetime("2026-01-15 09:30:00")
    assert rules.is_valid_datetime("20260115093000")
    assert not rules.is_valid_datetime("2026-01-15")


def test_icd10():
    assert rules.is_valid_icd10("A00")
    assert rules.is_valid_icd10("J45.0")
    assert rules.is_valid_icd10("Z000")
    assert not rules.is_valid_icd10("12345")
    assert not rules.is_valid_icd10("")
