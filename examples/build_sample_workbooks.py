from pathlib import Path

from openpyxl import Workbook

output_dir = Path(__file__).parent / "workbooks"
output_dir.mkdir(exist_ok=True)
samples = {
    "january.xlsx": [[" Alice Johnson ", "2026-03-04", 120], ["Bob Smith", "03/05/2026", 80]],
    "february.xlsx": [["Alice Johnson", "03/04/2026", 120], ["Carol 张", "March 7, 2026", 150]],
    "march.xlsx": [["Dan Brown", "not-a-date", 95], ["Eve Davis", "2026/03/09", "unknown"]],
    "april.xlsx": [["Frank Miller", "2026-04-01", 60], [None, None, None]],
}
for filename, rows in samples.items():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["Name", "Date", "Amount"])
    for row in rows:
        sheet.append(row)
    workbook.save(output_dir / filename)
print(f"Created {len(samples)} fictional sample workbooks in {output_dir}")
