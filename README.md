# CSV Rescue Kit

Clean a messy CSV without changing the original, and get a JSON report showing exactly what changed and what still needs human review.

## What it does

- Normalizes column names and resolves duplicate headers.
- Trims surrounding whitespace and removes empty rows.
- Removes exact duplicate rows after trimming.
- Lowercases email addresses and flags invalid values without inventing corrections.
- Optionally normalizes dates to ISO `YYYY-MM-DD`; ambiguous slash dates use US month-first order.
- Detects comma, tab, semicolon, and pipe delimiters.
- Preserves the source file and writes a separate cleaned CSV plus audit report.

This is a deterministic cleanup tool, not a promise that automatically cleaned data is correct. Review the flagged values before using the output for business decisions.

## Run

Python 3.10+; no third-party runtime packages required.

```bash
python csv_rescue.py examples/messy_customers.csv \
  --output examples/clean_customers.csv \
  --report examples/cleanup_report.json \
  --date-columns signup_date
```

The command prints the summary and writes both deliverables. The included example contains fictional data only.

## Consolidate Excel workbooks

Merge the active sheet from multiple `.xlsx` files, retain selected columns, normalize dates, remove exact duplicates, and produce a review report. This command requires `openpyxl`; the CSV-only command has no third-party runtime dependencies.

```bash
python excel_consolidate.py examples/workbooks/*.xlsx \
  --columns name,date,amount \
  --output examples/consolidated_master.xlsx \
  --report examples/consolidation_report.json
```

The included four workbooks contain fictional data. Regenerate them with `python examples/build_sample_workbooks.py`. Column names are normalized before matching, and every requested column must exist in every source workbook.

## Development check

```bash
python -m pytest
```

## Service experiment

A fixed-scope, human-reviewed CSV cleanup service using this toolkit is described in [OFFER.md](OFFER.md). To discuss a redacted sample, [open a public service inquiry](https://github.com/difeizheng/csv-rescue-kit/issues/new?template=service-inquiry.yml); never post sensitive data. No paid orders or revenue are claimed yet.
