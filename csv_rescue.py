#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d %b %Y",
    "%B %d, %Y",
)


def normalized_headers(fieldnames):
    headers = []
    seen = {}
    for index, value in enumerate(fieldnames or [], start=1):
        base = re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")
        base = base or f"column_{index}"
        seen[base] = seen.get(base, 0) + 1
        headers.append(base if seen[base] == 1 else f"{base}_{seen[base]}")
    return headers


def parse_date(value):
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            pass
    return None


def clean_file(input_path, output_path, report_path, date_columns=()):
    input_path = Path(input_path)
    output_path = Path(output_path)
    report_path = Path(report_path)
    date_columns = set(date_columns)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        sample = source.read(8192)
        source.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(source, dialect)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise ValueError("Input CSV is empty.") from None
        headers = normalized_headers(raw_headers)
        unknown_date_columns = date_columns.difference(headers)
        if unknown_date_columns:
            raise ValueError(f"Unknown date columns: {', '.join(sorted(unknown_date_columns))}")

        stats = {
            "input_rows": 0,
            "output_rows": 0,
            "empty_rows_removed": 0,
            "duplicate_rows_removed": 0,
            "whitespace_cells_trimmed": 0,
            "emails_normalized": 0,
            "dates_normalized": 0,
        }
        invalid_emails = []
        unparsed_dates = []
        seen_rows = set()
        cleaned_rows = []

        for row in reader:
            stats["input_rows"] += 1
            padded = row[: len(headers)] + [""] * max(0, len(headers) - len(row))
            cleaned = []
            for value in padded:
                stripped = value.strip()
                stats["whitespace_cells_trimmed"] += value != stripped
                cleaned.append(stripped)
            if not any(cleaned):
                stats["empty_rows_removed"] += 1
                continue

            record = dict(zip(headers, cleaned))
            if "email" in record and record["email"]:
                lowered = record["email"].lower()
                stats["emails_normalized"] += lowered != record["email"]
                record["email"] = lowered
                if not EMAIL_RE.match(lowered):
                    invalid_emails.append({"input_row": stats["input_rows"], "value": lowered})
            for column in date_columns:
                value = record[column]
                if not value:
                    continue
                parsed = parse_date(value)
                if parsed:
                    stats["dates_normalized"] += parsed != value
                    record[column] = parsed
                else:
                    unparsed_dates.append({"input_row": stats["input_rows"], "column": column, "value": value})

            row_key = tuple(record[column] for column in headers)
            if row_key in seen_rows:
                stats["duplicate_rows_removed"] += 1
                continue
            seen_rows.add(row_key)
            cleaned_rows.append([record[column] for column in headers])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.writer(destination, dialect=csv.excel, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(cleaned_rows)

    stats["output_rows"] = len(cleaned_rows)
    report = {
        "source_file": input_path.name,
        "cleaned_file": output_path.name,
        "delimiter": repr(dialect.delimiter),
        "columns": headers,
        "summary": stats,
        "issues_requiring_review": {
            "invalid_emails": invalid_emails,
            "unparsed_dates": unparsed_dates,
        },
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="Clean a CSV and produce an auditable JSON report.")
    parser.add_argument("input", help="Source CSV (never modified)")
    parser.add_argument("--output", required=True, help="Cleaned CSV path")
    parser.add_argument("--report", required=True, help="JSON report path")
    parser.add_argument("--date-columns", default="", help="Comma-separated normalized column names")
    args = parser.parse_args()
    date_columns = [value.strip() for value in args.date_columns.split(",") if value.strip()]
    try:
        report = clean_file(args.input, args.output, args.report, date_columns)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
