"""The validation engine: check a loaded data file against a schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import rules
from .loader import DataFile
from .schema import Field, Schema

# Severity levels.
ERROR = "ERROR"
WARNING = "WARNING"


@dataclass
class Issue:
    """A single validation finding tied to a row/column."""

    row: int  # 1-based data row number (header is row 0)
    column: str
    rule: str
    severity: str
    message: str
    value: str = ""


@dataclass
class ValidationResult:
    schema_name: str
    total_rows: int
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == WARNING]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def rows_with_errors(self) -> int:
        return len({i.row for i in self.errors})


def _check_value(fld: Field, value: str) -> list[tuple[str, str, str]]:
    """Validate one cell. Returns a list of (rule, severity, message)."""
    findings: list[tuple[str, str, str]] = []
    v = value.strip()

    if v == "":
        if fld.required:
            findings.append(("required", ERROR, "missing required value"))
        return findings  # nothing else to check on an empty optional cell

    if fld.exact_length is not None and len(v) != fld.exact_length:
        findings.append((
            "exact_length", ERROR,
            f"length {len(v)} != required {fld.exact_length}",
        ))
    if fld.max_length is not None and len(v) > fld.max_length:
        findings.append((
            "max_length", ERROR,
            f"length {len(v)} exceeds max {fld.max_length}",
        ))

    t = fld.type
    if t == "cid":
        if not rules.is_valid_thai_cid(v):
            findings.append(("cid_checksum", ERROR,
                             "invalid Thai national ID (check digit/format)"))
    elif t == "date":
        if rules.is_buddhist_era_year(v):
            findings.append(("date_buddhist_era", ERROR,
                             "date appears to use Buddhist era (พ.ศ.); "
                             "expected Gregorian (ค.ศ.) YYYYMMDD"))
        elif not rules.is_valid_date_yyyymmdd(v):
            findings.append(("date_format", ERROR,
                             "invalid date; expected YYYYMMDD"))
    elif t == "datetime":
        if not rules.is_valid_datetime(v):
            findings.append(("datetime_format", ERROR,
                             "invalid datetime; expected 'YYYY-MM-DD HH:MM:SS'"))
    elif t == "time":
        if not rules.is_valid_time(v):
            findings.append(("time_format", WARNING,
                             "unrecognised time format"))
    elif t == "icd10":
        if not rules.is_valid_icd10(v):
            findings.append(("icd10_format", WARNING,
                             "does not look like a valid ICD-10 code"))
    elif t == "int":
        if not rules.is_int(v):
            findings.append(("int_format", ERROR, "not an integer"))
    elif t == "decimal":
        if not rules.is_decimal(v):
            findings.append(("decimal_format", ERROR, "not a number"))

    # Numeric range checks (only when the value parses as a number).
    if fld.min is not None or fld.max is not None:
        if rules.is_decimal(v):
            num = float(v)
            if fld.min is not None and num < fld.min:
                findings.append(("range_min", WARNING,
                                 f"value {num} below expected min {fld.min}"))
            if fld.max is not None and num > fld.max:
                findings.append(("range_max", WARNING,
                                 f"value {num} above expected max {fld.max}"))

    # Allowed code set.
    if fld.allowed is not None and v not in fld.allowed:
        findings.append(("allowed_values", ERROR,
                         f"'{v}' not in allowed set {fld.allowed}"))

    return findings


def validate(data: DataFile, schema: Schema) -> ValidationResult:
    """Validate a loaded :class:`DataFile` against a :class:`Schema`."""
    result = ValidationResult(schema_name=schema.name, total_rows=len(data.rows))

    # 1. Header / structure checks.
    present = set(data.header)
    for fld in schema.fields:
        if fld.name not in present:
            sev = ERROR if fld.required else WARNING
            result.issues.append(Issue(
                row=0, column=fld.name, rule="missing_column", severity=sev,
                message=f"expected column '{fld.name}' not found in file",
            ))
    extras = [h for h in data.header if schema.field(h) is None]
    for col in extras:
        result.issues.append(Issue(
            row=0, column=col, rule="unexpected_column", severity=WARNING,
            message=f"column '{col}' is not part of the {schema.name} schema",
        ))

    # 2. Per-cell checks + primary-key duplicate detection.
    seen_keys: dict[tuple[str, ...], int] = {}
    pk = [k for k in schema.primary_key if k in present]

    for idx, record in enumerate(data.as_dicts(), start=1):
        for fld in schema.fields:
            if fld.name not in present:
                continue
            value = record.get(fld.name, "")
            for rule_name, severity, msg in _check_value(fld, value):
                result.issues.append(Issue(
                    row=idx, column=fld.name, rule=rule_name,
                    severity=severity, message=msg, value=value,
                ))

        if pk:
            key = tuple(record.get(k, "") for k in pk)
            if all(part != "" for part in key):
                if key in seen_keys:
                    result.issues.append(Issue(
                        row=idx, column="+".join(pk), rule="duplicate_key",
                        severity=ERROR,
                        message=f"duplicate primary key {key} "
                                f"(first seen at row {seen_keys[key]})",
                        value="|".join(key),
                    ))
                else:
                    seen_keys[key] = idx

    return result
