"""Command-line interface for moph-report.

Examples
--------
    moph-report list-schemas
    moph-report describe PERSON
    moph-report validate person.txt --schema PERSON
    moph-report validate person.txt --schema PERSON --out person.errors.csv
    moph-report summary service.txt --schema SERVICE
    moph-report check-cid 1101700203451
"""

from __future__ import annotations

import argparse
import sys

from . import __version__, crosscheck, loader, report
from .rules import is_valid_thai_cid
from .schema import list_schemas, load_schema, load_schema_file
from .validator import validate


def _resolve_schema(args):
    if getattr(args, "schema_file", None):
        return load_schema_file(args.schema_file)
    return load_schema(args.schema)


def cmd_list_schemas(args) -> int:
    for name in list_schemas():
        schema = load_schema(name)
        print(f"{name:<16} {schema.thai_name}")
    return 0


def cmd_describe(args) -> int:
    if not args.schema and not args.schema_file:
        print("error: provide a schema name (e.g. 'describe PERSON') "
              "or --schema-file", file=sys.stderr)
        return 2
    schema = _resolve_schema(args)
    print(f"{schema.name} — {schema.thai_name}")
    if schema.description:
        print(schema.description)
    print(f"Delimiter: {schema.delimiter!r}   "
          f"Primary key: {', '.join(schema.primary_key) or '(none)'}")
    print("\nFields:")
    print(f"  {'NAME':<18}{'TYPE':<10}{'REQ':<5}DESCRIPTION")
    for f in schema.fields:
        req = "yes" if f.required else ""
        print(f"  {f.name:<18}{f.type:<10}{req:<5}{f.thai}")
    return 0


def cmd_validate(args) -> int:
    schema = _resolve_schema(args)
    data = loader.load(args.file, delimiter=args.delimiter, encoding=args.encoding)
    result = validate(data, schema)

    report.print_validation_summary(result, sys.stdout)

    if args.out:
        report.write_issues_csv(result, args.out)
        print(f"\nFull issue report written to: {args.out}")
    if args.json:
        report.write_result_json(result, args.json)
        print(f"JSON result written to:       {args.json}")
    if args.xlsx:
        report.write_issues_xlsx(result, args.xlsx)
        print(f"Excel report written to:      {args.xlsx}")

    # Non-zero exit code on failure so this is CI/script friendly.
    return 0 if result.is_valid else 1


def cmd_summary(args) -> int:
    schema = _resolve_schema(args)
    data = loader.load(args.file, delimiter=args.delimiter, encoding=args.encoding)
    summary = report.build_summary(data, schema)
    report.print_summary(summary, sys.stdout)
    if args.json:
        import json
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
        print(f"\nSummary written to: {args.json}")
    if args.xlsx:
        report.write_summary_xlsx(summary, args.xlsx)
        print(f"\nExcel summary written to: {args.xlsx}")
    return 0


def _parse_crosscheck_inputs(tokens):
    """Turn ``SCHEMA=path`` / bare ``path`` tokens into {SCHEMA: DataFile}.

    A bare path infers its schema from the filename stem (e.g. ``service.txt``
    -> SERVICE) when that matches a bundled schema.
    """
    bundled = set(list_schemas())
    files = {}
    for token in tokens:
        if "=" in token:
            name, _, path = token.partition("=")
            name = name.strip().upper()
        else:
            path = token
            import os
            stem = os.path.splitext(os.path.basename(path))[0]
            # Strip a common "_sample" suffix and uppercase to match schema names.
            name = stem.replace("_sample", "").replace("_with_errors", "").upper()
        if name not in bundled:
            raise SystemExit(
                f"cannot determine a known schema for '{token}'. "
                f"Use SCHEMA=path, e.g. SERVICE={path}. "
                f"Known schemas: {', '.join(sorted(bundled))}")
        files[name] = loader.load(path)
    return files


def cmd_crosscheck(args) -> int:
    files = _parse_crosscheck_inputs(args.inputs)
    result = crosscheck.crosscheck(files)
    crosscheck.print_crosscheck(result, sys.stdout)
    return 0 if result.is_valid else 1


def cmd_check_cid(args) -> int:
    ok = is_valid_thai_cid(args.cid)
    print(f"{args.cid}: {'VALID' if ok else 'INVALID'}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="moph-report",
        description="Validate and summarize MOPH Thailand 43-file datasets.",
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # Shared schema-selection options.
    def add_schema_opts(p, required=True):
        g = p.add_mutually_exclusive_group(required=required)
        g.add_argument("--schema", help="bundled schema name, e.g. PERSON")
        g.add_argument("--schema-file", help="path to a custom schema JSON file")

    p_list = sub.add_parser("list-schemas", help="list bundled 43-file schemas")
    p_list.set_defaults(func=cmd_list_schemas)

    p_desc = sub.add_parser("describe", help="show a schema's fields")
    p_desc.add_argument("schema", nargs="?", help="bundled schema name, e.g. PERSON")
    p_desc.add_argument("--schema-file", help="path to a custom schema JSON file")
    p_desc.set_defaults(func=cmd_describe)

    p_val = sub.add_parser("validate", help="validate a data file against a schema")
    p_val.add_argument("file", help="path to the delimited 43-file export")
    add_schema_opts(p_val)
    p_val.add_argument("--delimiter", help="field delimiter (default: auto-detect)")
    p_val.add_argument("--encoding", help="file encoding (default: auto-detect)")
    p_val.add_argument("--out", help="write the full issue report to this CSV path")
    p_val.add_argument("--json", help="write a machine-readable JSON result")
    p_val.add_argument("--xlsx", help="write an Excel (.xlsx) report "
                       "(needs the optional 'openpyxl' package)")
    p_val.set_defaults(func=cmd_validate)

    p_sum = sub.add_parser("summary", help="show aggregate stats for a data file")
    p_sum.add_argument("file", help="path to the delimited 43-file export")
    add_schema_opts(p_sum)
    p_sum.add_argument("--delimiter", help="field delimiter (default: auto-detect)")
    p_sum.add_argument("--encoding", help="file encoding (default: auto-detect)")
    p_sum.add_argument("--json", help="write the summary to this JSON path")
    p_sum.add_argument("--xlsx", help="write the summary to this Excel (.xlsx) path "
                       "(needs the optional 'openpyxl' package)")
    p_sum.set_defaults(func=cmd_summary)

    p_cross = sub.add_parser(
        "crosscheck",
        help="check referential integrity across several 43-file exports")
    p_cross.add_argument(
        "inputs", nargs="+",
        help="files to cross-check as SCHEMA=path (e.g. PERSON=person.txt "
             "SERVICE=service.txt); a bare path infers the schema from its name")
    p_cross.set_defaults(func=cmd_crosscheck)

    p_cid = sub.add_parser("check-cid", help="validate a single Thai national ID")
    p_cid.add_argument("cid", help="13-digit Thai national ID")
    p_cid.set_defaults(func=cmd_check_cid)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except BrokenPipeError:
        # Output was piped to a command that closed early (e.g. `| head`).
        return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
