"""Cross-file referential integrity checks across several 43-file exports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TextIO

from .loader import DataFile
from .relationships import RELATIONSHIPS, Relationship


@dataclass
class CrossIssue:
    relationship: str
    child: str
    child_row: int  # 1-based data row in the child file
    key: str
    message: str


@dataclass
class CrossCheckResult:
    checked: list[str] = field(default_factory=list)  # relationship descriptions
    skipped: list[str] = field(default_factory=list)  # why a relationship was skipped
    issues: list[CrossIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0


def _has_columns(data: DataFile, keys: tuple[str, ...]) -> bool:
    present = set(data.header)
    return all(k in present for k in keys)


def _key_set(data: DataFile, keys: tuple[str, ...]) -> set[tuple[str, ...]]:
    result: set[tuple[str, ...]] = set()
    for record in data.as_dicts():
        key = tuple(record.get(k, "").strip() for k in keys)
        if all(part != "" for part in key):
            result.add(key)
    return result


def crosscheck(files: dict[str, DataFile],
               relationships: list[Relationship] | None = None) -> CrossCheckResult:
    """Check referential integrity across the supplied files.

    ``files`` maps an UPPER-CASE schema name to its loaded :class:`DataFile`.
    Only relationships whose child *and* parent files are both present are
    checked; others are recorded in ``skipped``.
    """
    rels = relationships if relationships is not None else RELATIONSHIPS
    result = CrossCheckResult()

    for rel in rels:
        if rel.child not in files or rel.parent not in files:
            continue  # not enough files supplied to evaluate this relationship

        child_data = files[rel.child]
        parent_data = files[rel.parent]

        if not _has_columns(child_data, rel.child_keys):
            result.skipped.append(
                f"{rel.description}: child missing key column(s)")
            continue
        if not _has_columns(parent_data, rel.parent_keys):
            result.skipped.append(
                f"{rel.description}: parent missing key column(s)")
            continue

        result.checked.append(rel.description)
        parent_keys = _key_set(parent_data, rel.parent_keys)

        for idx, record in enumerate(child_data.as_dicts(), start=1):
            key = tuple(record.get(k, "").strip() for k in rel.child_keys)
            if any(part == "" for part in key):
                continue  # blank keys are a per-file (schema) concern, not here
            if key not in parent_keys:
                result.issues.append(CrossIssue(
                    relationship=rel.description,
                    child=rel.child,
                    child_row=idx,
                    key="|".join(key),
                    message=f"no matching {rel.parent} row for "
                            f"{'+'.join(rel.child_keys)}={'|'.join(key)}",
                ))

    return result


def print_crosscheck(result: CrossCheckResult, out: TextIO) -> None:
    status = "PASS" if result.is_valid else "FAIL"
    out.write("Relationships checked:\n")
    for desc in result.checked:
        out.write(f"  ✓ {desc}\n")
    if not result.checked:
        out.write("  (none — supply two or more related files)\n")
    if result.skipped:
        out.write("\nSkipped:\n")
        for s in result.skipped:
            out.write(f"  - {s}\n")
    out.write(f"\nOrphan references: {len(result.issues)}\n")
    out.write(f"Result: {status}\n")

    preview = result.issues[:15]
    if preview:
        out.write("\nFirst orphan references:\n")
        for i in preview:
            out.write(f"  [{i.child} row {i.child_row}] {i.message}\n")
        if len(result.issues) > len(preview):
            out.write(f"  ... and {len(result.issues) - len(preview)} more\n")
