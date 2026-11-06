"""Headless command-line interface for NumberScope.

Examples:
    python cli.py +919876543210
    python cli.py 9876543210 --region IN
    python cli.py +14155552671 --json
    python cli.py +919876543210 +442071838750 --csv > report.csv

The same local analysis as the Streamlit app, with no network access.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys

from numberscope import NumberReport, analyse_number, metadata_version


def _render_text(report: NumberReport) -> str:
    lines = [
        f"Input:                {report.input}",
        f"International:        {report.international}",
        f"National:            {report.national}",
        f"E.164:               {report.e164}",
        f"Country code:        {report.country_calling_code}",
        f"Region:              {report.region_code}",
        f"Number type:         {report.number_type}",
        f"Possible length:     {report.possible} ({report.possible_reason})",
        f"Valid range:         {report.valid_range}",
        f"Carrier (range):     {report.carrier_metadata}",
        f"Geographic range:    {report.range_description}",
        f"Time zones:          {', '.join(report.time_zones)}",
        f"Analysed at (UTC):   {report.analysed_at_utc}",
        f"Metadata version:    {report.metadata_version}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="numberscope",
        description="Analyse public phone-number numbering-plan metadata locally.",
    )
    parser.add_argument("numbers", nargs="+", help="One or more phone numbers.")
    parser.add_argument(
        "--region",
        default="IN",
        help="Default region for numbers without a leading '+' (default: IN).",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--json", action="store_true", help="Emit JSON.")
    group.add_argument("--csv", action="store_true", help="Emit CSV.")
    parser.add_argument(
        "--version", action="version", version=f"libphonenumber metadata {metadata_version()}"
    )
    args = parser.parse_args(argv)

    reports: list[NumberReport] = []
    errors: list[str] = []
    for number in args.numbers:
        try:
            reports.append(analyse_number(number, args.region))
        except ValueError as exc:
            errors.append(f"{number}: {exc}")

    if args.json:
        print(json.dumps([r.as_dict() for r in reports], indent=2))
    elif args.csv:
        buffer = io.StringIO()
        if reports:
            writer = csv.DictWriter(buffer, fieldnames=list(reports[0].as_flat_row()))
            writer.writeheader()
            for report in reports:
                writer.writerow(report.as_flat_row())
        sys.stdout.write(buffer.getvalue())
    else:
        print(("\n" + "-" * 40 + "\n").join(_render_text(r) for r in reports))

    for message in errors:
        print(f"[error] {message}", file=sys.stderr)

    return 1 if errors and not reports else 0


if __name__ == "__main__":
    raise SystemExit(main())
