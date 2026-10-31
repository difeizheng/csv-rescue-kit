import csv
import json

import pytest

from csv_rescue import clean_file


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.reader(source))


def test_cleans_headers_whitespace_duplicates_and_empty_rows(tmp_path):
    source = tmp_path / "messy.csv"
    source.write_text(
        " Full Name ,Email,Email\n"
        " Alice , ALICE@EXAMPLE.COM ,duplicate@example.com\n"
        "\n"
        "Alice,alice@example.com,duplicate@example.com\n"
        " Bob , BOB@EXAMPLE.COM ,second@example.com\n",
        encoding="utf-8",
    )
    output = tmp_path / "clean.csv"
    report_path = tmp_path / "report.json"

    report = clean_file(source, output, report_path)

    assert read_rows(output) == [
        ["full_name", "email", "email_2"],
        ["Alice", "alice@example.com", "duplicate@example.com"],
        ["Bob", "bob@example.com", "second@example.com"],
    ]
    assert report["summary"] == {
        "input_rows": 4,
        "output_rows": 2,
        "empty_rows_removed": 1,
        "duplicate_rows_removed": 1,
        "whitespace_cells_trimmed": 4,
        "emails_normalized": 2,
        "dates_normalized": 0,
    }
    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_normalizes_dates_and_flags_review_items(tmp_path):
    source = tmp_path / "dates.csv"
    source.write_text(
        "email,signup_date\nBAD EMAIL,03/04/2026\na@example.com,not-a-date\n",
        encoding="utf-8",
    )
    report = clean_file(source, tmp_path / "out.csv", tmp_path / "report.json", ["signup_date"])

    assert read_rows(tmp_path / "out.csv")[1:] == [
        ["bad email", "2026-03-04"],
        ["a@example.com", "not-a-date"],
    ]
    assert report["issues_requiring_review"]["invalid_emails"][0]["value"] == "bad email"
    assert report["issues_requiring_review"]["unparsed_dates"][0]["value"] == "not-a-date"


def test_detects_semicolon_delimiter(tmp_path):
    source = tmp_path / "semi.csv"
    source.write_text("Name;Amount\n Alice ; 42 \n", encoding="utf-8")
    report = clean_file(source, tmp_path / "out.csv", tmp_path / "report.json")

    assert read_rows(tmp_path / "out.csv") == [["name", "amount"], ["Alice", "42"]]
    assert report["delimiter"] == "';'"


def test_rejects_unknown_date_column(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("email\na@example.com\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown date columns"):
        clean_file(source, tmp_path / "out.csv", tmp_path / "report.json", ["missing"])


def test_empty_input_has_clear_error(tmp_path):
    source = tmp_path / "empty.csv"
    source.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Input CSV is empty"):
        clean_file(source, tmp_path / "out.csv", tmp_path / "report.json")
