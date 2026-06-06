"""Reading delimited 43-file data exports.

43-file exports are delimited text files (traditionally pipe ``|`` separated)
with a header row. They are commonly encoded in UTF-8, but older HIS exports use
TIS-620 / CP874 (Thai). This loader auto-detects the encoding and delimiter.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Iterator, Optional

_ENCODINGS = ("utf-8-sig", "utf-8", "cp874", "tis-620")
_DELIMITERS = ("|", "\t", ",", ";")


@dataclass
class DataFile:
    """A loaded delimited file: its header plus an iterator of rows."""

    header: list[str]
    rows: list[list[str]]
    delimiter: str
    encoding: str

    def as_dicts(self) -> Iterator[dict[str, str]]:
        for row in self.rows:
            # Pad/truncate defensively so zip aligns with the header.
            padded = row + [""] * (len(self.header) - len(row))
            yield dict(zip(self.header, padded))


def detect_encoding(path: str) -> str:
    for enc in _ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as fh:
                fh.read()
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Fall back to utf-8 with replacement so we never hard-crash on a stray byte.
    return "utf-8"


def detect_delimiter(sample: str) -> str:
    first_line = sample.splitlines()[0] if sample.splitlines() else ""
    counts = {d: first_line.count(d) for d in _DELIMITERS}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else "|"


def load(path: str, delimiter: Optional[str] = None,
         encoding: Optional[str] = None) -> DataFile:
    """Load a delimited 43-file export.

    ``delimiter`` and ``encoding`` are auto-detected when not supplied.
    """
    enc = encoding or detect_encoding(path)
    with open(path, "r", encoding=enc, errors="replace", newline="") as fh:
        text = fh.read()

    delim = delimiter or detect_delimiter(text)
    reader = csv.reader(text.splitlines(), delimiter=delim)
    records = list(reader)
    if not records:
        return DataFile(header=[], rows=[], delimiter=delim, encoding=enc)

    header = [h.strip() for h in records[0]]
    rows = [r for r in records[1:] if any(cell.strip() for cell in r)]
    return DataFile(header=header, rows=rows, delimiter=delim, encoding=enc)
