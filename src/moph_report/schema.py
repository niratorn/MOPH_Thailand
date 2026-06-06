"""Loading and representing 43-file schema definitions.

Schemas live as JSON files in the ``schemas/`` directory. Each describes one of
the standard 43 files: its fields, types, required-ness, allowed code values and
the primary key used for duplicate detection.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from typing import Any, Optional


@dataclass
class Field:
    """A single column definition within a 43-file schema."""

    name: str
    type: str = "string"
    required: bool = False
    thai: str = ""
    max_length: Optional[int] = None
    exact_length: Optional[int] = None
    allowed: Optional[list[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Field":
        return cls(
            name=data["name"],
            type=data.get("type", "string"),
            required=bool(data.get("required", False)),
            thai=data.get("thai", ""),
            max_length=data.get("max_length"),
            exact_length=data.get("exact_length"),
            allowed=data.get("allowed"),
            min=data.get("min"),
            max=data.get("max"),
            notes=data.get("notes", ""),
        )


@dataclass
class Schema:
    """A complete 43-file definition."""

    name: str
    thai_name: str = ""
    description: str = ""
    delimiter: str = "|"
    primary_key: list[str] = field(default_factory=list)
    fields: list[Field] = field(default_factory=list)

    @property
    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]

    def field(self, name: str) -> Optional[Field]:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schema":
        return cls(
            name=data["name"],
            thai_name=data.get("thai_name", ""),
            description=data.get("description", ""),
            delimiter=data.get("delimiter", "|"),
            primary_key=list(data.get("primary_key", [])),
            fields=[Field.from_dict(f) for f in data.get("fields", [])],
        )


def _schema_resource(name: str) -> Optional[str]:
    """Return the packaged JSON filename for a schema name, or None."""
    filename = f"{name.lower()}.json"
    pkg = resources.files("moph_report.schemas")
    if pkg.joinpath(filename).is_file():
        return filename
    return None


def list_schemas() -> list[str]:
    """Return the names of all bundled schemas, upper-cased."""
    pkg = resources.files("moph_report.schemas")
    names = []
    for entry in pkg.iterdir():
        if entry.name.endswith(".json"):
            names.append(entry.name[:-5].upper())
    return sorted(names)


def load_schema(name: str) -> Schema:
    """Load a bundled schema by name (case-insensitive), e.g. ``"PERSON"``.

    Raises ``KeyError`` if no schema with that name is bundled.
    """
    filename = _schema_resource(name)
    if filename is None:
        available = ", ".join(list_schemas())
        raise KeyError(
            f"Unknown schema '{name}'. Available schemas: {available}"
        )
    text = resources.files("moph_report.schemas").joinpath(filename).read_text(
        encoding="utf-8"
    )
    return Schema.from_dict(json.loads(text))


def load_schema_file(path: str) -> Schema:
    """Load a schema from an arbitrary JSON file path (for custom schemas)."""
    with open(path, "r", encoding="utf-8") as fh:
        return Schema.from_dict(json.load(fh))
