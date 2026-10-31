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

## Development check

```bash
python -m pytest
```

## Service experiment

A fixed-scope, human-reviewed CSV cleanup service using this toolkit is described in [OFFER.md](OFFER.md). No paid orders or revenue are claimed yet.
