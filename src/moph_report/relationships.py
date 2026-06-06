"""Declarative referential relationships between 43-file schemas.

Each :class:`Relationship` says: every row in ``child`` (matched on
``child_keys``) must have a corresponding row in ``parent`` (matched on
``parent_keys``). These mirror how the 43 files link together — visit detail
files point back to SERVICE, and person-level files point back to PERSON.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Relationship:
    child: str
    child_keys: tuple[str, ...]
    parent: str
    parent_keys: tuple[str, ...]

    @property
    def description(self) -> str:
        ck = "+".join(self.child_keys)
        pk = "+".join(self.parent_keys)
        return f"{self.child}.{ck} -> {self.parent}.{pk}"


# The default relationship set. `PID` is the per-hospital person id that links
# the visit/person files together; visit-detail files additionally share `SEQ`.
RELATIONSHIPS: list[Relationship] = [
    Relationship("SERVICE", ("PID",), "PERSON", ("PID",)),
    Relationship("DIAGNOSIS_OPD", ("PID", "SEQ"), "SERVICE", ("PID", "SEQ")),
    Relationship("DRUG_OPD", ("PID", "SEQ"), "SERVICE", ("PID", "SEQ")),
    Relationship("CHARGE_OPD", ("PID", "SEQ"), "SERVICE", ("PID", "SEQ")),
    Relationship("APPOINTMENT", ("PID", "SEQ"), "SERVICE", ("PID", "SEQ")),
    Relationship("CHRONIC", ("PID",), "PERSON", ("PID",)),
    Relationship("DEATH", ("CID",), "PERSON", ("CID",)),
    Relationship("ADDRESS", ("CID",), "PERSON", ("CID",)),
]
