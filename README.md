# moph-report

**Validation & reporting tools for MOPH Thailand 43-file (43 แฟ้ม) hospital datasets.**

Hospitals under the Ministry of Public Health (MOPH / กระทรวงสาธารณสุข) must
regularly export the standardized **43-file dataset** and submit it to the
Health Data Center (HDC). When the data has structural problems — missing
fields, wrong date formats, invalid codes, malformed national IDs, duplicate
records — submissions get **rejected**, and staff spend hours hunting down the
cause by hand.

`moph-report` is a small command-line tool that **checks a 43-file export
*before* you submit it** and produces a clear, row-by-row report of what needs
fixing. It also generates quick summary statistics for monthly review.

> 🎯 **Goal:** reduce the manual data-checking burden on healthcare workers and
> hospital IT staff, and cut down on rejected HDC submissions.

## Highlights

- ✅ **Validates against MOPH 43-file structure** — required columns, field
  lengths, data types, and allowed code sets.
- 🆔 **Thai national ID (เลขบัตรประชาชน) check-digit validation** — catches
  typo'd or fabricated 13-digit IDs.
- 📅 **Date sanity checks** — flags the common Buddhist-era (พ.ศ.) vs.
  Gregorian (ค.ศ.) mix-up and invalid calendar dates.
- 🔁 **Duplicate detection** on each file's primary key.
- 📊 **Summary reports** — e.g. sex distribution, diagnosis-type counts.
- 🧰 **Zero dependencies** — pure Python standard library. Runs offline on a
  stock Python 3.9+ install. Reads UTF-8 *and* legacy TIS-620/CP874 exports.
- 🤖 **Script/CI-friendly** — exits non-zero when validation fails.

## Bundled schemas

| File | Thai | Description |
|------|------|-------------|
| `PERSON` | ข้อมูลทั่วไปของประชาชน | Demographics of people in the catchment area |
| `SERVICE` | การรับบริการผู้ป่วยนอก | Outpatient (OPD) service visits |
| `DIAGNOSIS_OPD` | การวินิจฉัยผู้ป่วยนอก | Outpatient ICD-10 diagnoses |
| `DEATH` | ข้อมูลการตาย | Death records |

More of the 43 files can be added by dropping a JSON schema into
`src/moph_report/schemas/` (or pass your own with `--schema-file`).

## Installation

```bash
# From the project root
pip install -e .
```

Or run it without installing, straight from the source tree:

```bash
PYTHONPATH=src python -m moph_report.cli --help
```

## Usage

```bash
# See which 43-file schemas are bundled
moph-report list-schemas

# Inspect a schema's fields
moph-report describe PERSON

# Validate an exported file (auto-detects delimiter & encoding)
moph-report validate person.txt --schema PERSON

# Write a full, reviewable error report to CSV
moph-report validate person.txt --schema PERSON --out person.errors.csv

# Quick aggregate stats for a monthly sanity check
moph-report summary service.txt --schema SERVICE

# Validate a single Thai national ID
moph-report check-cid 1101700203450
```

### Example

Try it against the bundled sample that intentionally contains mistakes:

```bash
moph-report validate examples/person_with_errors.txt --schema PERSON
```

You'll see it catch a bad national-ID check digit, a Buddhist-era birth date,
out-of-range codes, a missing required field, and a duplicate record.

## Privacy & safety

⚠️ Real 43-file exports contain **patient personal data (PII)**. Never commit
real data to this repository — the `.gitignore` already excludes common data
paths (`data/`, `*.dat`, `private_*.csv`). This tool runs **entirely locally**
and sends nothing over the network.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Disclaimer

This is a community helper tool. The bundled schemas cover a representative
subset of the 43 files and reflect the common public structure of the standard;
they are **not** an official MOPH/HDC release. Always confirm against the
current official 43-file structure specification for your reporting year before
relying on results for submission.

## License

MIT
