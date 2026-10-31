from datetime import datetime

import pytest
from openpyxl import Workbook, load_workbook

from excel_consolidate import consolidate_files


def make_workbook(path, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([" Name ", " Date ", "Amount"])
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_consolidates_workbooks_normalizes_and_deduplicates(tmp_path):
    first = tmp_path / "first.xlsx"
    second = tmp_path / "second.xlsx"
    make_workbook(first, [[" Alice ", datetime(2026, 3, 4), 10], ["Bob", "03/05/2026", 20]])
    make_workbook(second, [["Alice", "2026-03-04", 10], ["Carol", "bad-date", "unknown"], [None, None, None]])
    output = tmp_path / "master.xlsx"

    report = consolidate_files([first, second], output, tmp_path / "report.json", ["name", "date", "amount"])

    sheet = load_workbook(output, data_only=True).active
    assert list(sheet.values) == [
        ("name", "date", "amount"),
        ("Alice", "2026-03-04", 10),
        ("Bob", "2026-03-05", 20),
        ("Carol", "bad-date", "unknown"),
    ]
    assert report["summary"] == {
        "input_rows": 5,
        "empty_rows_removed": 1,
        "duplicate_rows_removed": 1,
        "output_rows": 3,
    }
    issues = report["issues_requiring_review"]
    assert {item["issue"] for item in issues} == {"unparsed_date", "non_numeric_amount"}


def test_missing_column_identifies_source_file(tmp_path):
    source = tmp_path / "missing.xlsx"
    workbook = Workbook()
    workbook.active.append(["name", "amount"])
    workbook.save(source)

    with pytest.raises(ValueError, match=r"missing.xlsx: missing columns: date"):
        consolidate_files([source], tmp_path / "out.xlsx", tmp_path / "report.json", ["name", "date", "amount"])


def test_rejects_duplicate_output_columns(tmp_path):
    with pytest.raises(ValueError, match="Output columns must be unique"):
        consolidate_files(["unused.xlsx"], tmp_path / "out.xlsx", tmp_path / "report.json", ["name", "name"])
