"""Reusable, low-level validation helpers.

These are pure functions with no I/O so they are easy to unit-test and reuse.
"""

from __future__ import annotations

import re
from datetime import datetime

# ICD-10 codes look like A00, A00.0, J45, Z00.0 etc. The 43-file export usually
# stores them without the dot (e.g. "A000"). Accept both forms.
_ICD10_RE = re.compile(r"^[A-Z][0-9]{2}\.?[0-9A-Z]{0,3}$")


def is_valid_thai_cid(cid: str) -> bool:
    """Validate a Thai national ID (13 digits) including its check digit.

    The check digit is the last digit. It is computed by multiplying the first
    12 digits by weights 13..2, summing, taking modulo 11, and subtracting from
    11 (mod 10).
    """
    if not cid or not cid.isdigit() or len(cid) != 13:
        return False
    total = sum(int(cid[i]) * (13 - i) for i in range(12))
    check = (11 - (total % 11)) % 10
    return check == int(cid[12])


def is_valid_date_yyyymmdd(value: str) -> bool:
    """True if ``value`` is a real calendar date in YYYYMMDD form.

    Accepts a Gregorian (ค.ศ.) year. Buddhist-era years (พ.ศ., > 2400) are
    rejected here so callers can flag the common BE/AD mix-up.
    """
    if not value or not value.isdigit() or len(value) != 8:
        return False
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        return False
    year = int(value[:4])
    return 1900 <= year <= 2200


def is_buddhist_era_year(value: str) -> bool:
    """Heuristic: an 8-digit date whose year looks like a Buddhist-era year."""
    if not value or not value.isdigit() or len(value) != 8:
        return False
    year = int(value[:4])
    return 2400 <= year <= 2700


def is_valid_datetime(value: str) -> bool:
    """True for the standard 43-file datetime format ``YYYY-MM-DD HH:MM:SS``.

    Also tolerates the compact ``YYYYMMDDHHMMSS`` form some exporters produce.
    """
    if not value:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def is_valid_time(value: str) -> bool:
    """True for HH:MM or HH:MM:SS or compact HHMMSS / HHMM."""
    if not value:
        return False
    for fmt in ("%H:%M:%S", "%H:%M", "%H%M%S", "%H%M"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def is_valid_icd10(value: str) -> bool:
    """True if ``value`` is a plausibly well-formed ICD-10 code."""
    if not value:
        return False
    return bool(_ICD10_RE.match(value.upper()))


def is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def is_decimal(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
