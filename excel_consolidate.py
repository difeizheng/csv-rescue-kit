#!/usr/bin/env python3
import argparse
import json
import numbers
import sys
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook

from csv_rescue import normalized_headers, parse_date


def iso_date(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return parse_date(value.strip())
    return None


def consolidate_files(input_paths, output_path, report_path, columns):
    columns = [column.strip().lower() for column in columns if column.strip()]
    if not columns:
        raise ValueError("At least one output column is required.")
    if len(set(columns)) != len(columns):
        raise ValueError("Output columns must be unique.")

    master_rows = []
    seen_rows = set()
    per_file = []
    review_items = []
    totals = {"input_rows": 0, "empty_rows_removed": 0, "duplicate_rows_removed": 0}

    for input_path_string in input_paths:
        input_path = Path(input_path_string)
        workbook = load_workbook(input_path, read_only=True, data_only=True)
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)
        try:
            raw_headers = next(rows)
        except StopIteration:
            workbook.close()
            raise ValueError(f"{input_path.name}: active sheet is empty.") from None
        headers = normalized_headers(["" if value is None else str(value) for value in raw_headers])
        positions = {}
        missing = [column for column in columns if column not in headers]
        if missing:
            workbook.close()
            raise ValueError(f"{input_path.name}: missing columns: {', '.join(missing)}")
        positions = {column: headers.index(column) for column in columns}

        file_stats = {"file": input_path.name, "sheet": sheet.title, "input_rows": 0, "kept_rows": 0}
        for source_row_number, row in enumerate(rows, start=2):
            file_stats["input_rows"] += 1
            totals["input_rows"] += 1
            record = {}
            for column, position in positions.items():
                value = row[position] if position < len(row) else None
                record[column] = value.strip() if isinstance(value, str) else value
            if all(value is None or value == "" for value in record.values()):
                totals["empty_rows_removed"] += 1
                continue

            for column in columns:
                value = record[column]
                if value is None or value == "":
                    review_items.append({"file": input_path.name, "row": source_row_number, "issue": "missing_value", "column": column})
                elif column == "date":
                    parsed = iso_date(value)
                    if parsed:
                        record[column] = parsed
                    else:
                        review_items.append({"file": input_path.name, "row": source_row_number, "issue": "unparsed_date", "value": str(value)})
                elif column == "amount" and (isinstance(value, bool) or not isinstance(value, numbers.Number)):
                    review_items.append({"file": input_path.name, "row": source_row_number, "issue": "non_numeric_amount", "value": str(value)})

            row_key = tuple(record[column] for column in columns)
            if row_key in seen_rows:
                totals["duplicate_rows_removed"] += 1
                continue
            seen_rows.add(row_key)
            master_rows.append([record[column] for column in columns])
            file_stats["kept_rows"] += 1
        per_file.append(file_stats)
        workbook.close()

    output_path = Path(output_path)
    report_path = Path(report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output = Workbook()
    sheet = output.active
    sheet.title = "Master"
    sheet.append(columns)
    for row in master_rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    output.save(output_path)

    report = {
        "output_file": output_path.name,
        "columns": columns,
        "summary": {**totals, "output_rows": len(master_rows)},
        "per_file": per_file,
        "issues_requiring_review": review_items,
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="Consolidate XLSX files into one deduplicated master table.")
    parser.add_argument("inputs", nargs="+", help="Source XLSX files (never modified)")
    parser.add_argument("--columns", required=True, help="Comma-separated normalized column names")
    parser.add_argument("--output", required=True, help="Output XLSX path")
    parser.add_argument("--report", required=True, help="JSON report path")
    args = parser.parse_args()
    columns = [value.strip() for value in args.columns.split(",") if value.strip()]
    try:
        report = consolidate_files(args.inputs, args.output, args.report, columns)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
