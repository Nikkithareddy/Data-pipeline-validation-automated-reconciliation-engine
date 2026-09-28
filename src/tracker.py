"""Writes an Excel execution tracker: run log, per-category summary, and schema/data error details."""
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

GREEN, RED, HEAD = "C6EFCE", "FFC7CE", "1F3864"


def _header(ws, cols):
    ws.append(cols)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=HEAD)
        cell.alignment = Alignment(horizontal="center")
    ws.freeze_panes = "A2"


def write_tracker(runs: dict, path: str) -> None:
    """runs = {"Before cleanup": [Result...], "After cleanup": [Result...]}"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Execution Tracker"
    _header(ws, ["Run", "Check ID", "Category", "Check", "Expected", "Actual", "Status", "Executed At"])
    for run, results in runs.items():
        for r in results:
            ws.append([run, r.check.check_id, r.check.category, r.check.name,
                       r.expected, r.actual, "PASS" if r.passed else "FAIL", r.executed_at])
            ws.cell(ws.max_row, 7).fill = PatternFill("solid", fgColor=GREEN if r.passed else RED)

    summ = wb.create_sheet("Summary")
    _header(summ, ["Run", "Category", "Checks", "Passed", "Failed", "Pass %"])
    for run, results in runs.items():
        by_cat = defaultdict(lambda: [0, 0])
        for r in results:
            by_cat[r.check.category][0] += 1
            by_cat[r.check.category][1] += r.passed
        for cat, (total, passed) in by_cat.items():
            summ.append([run, cat, total, passed, total - passed, round(100 * passed / total, 1)])
        total, passed = len(results), sum(r.passed for r in results)
        summ.append([run, "ALL", total, passed, total - passed, round(100 * passed / total, 1)])
        summ.cell(summ.max_row, 2).font = Font(bold=True)

    err = wb.create_sheet("Error Details")
    err.append(["Run", "Check ID", "Check", "Offending rows (first 20)"])
    for cell in err[1]:
        cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=HEAD)
    for run, results in runs.items():
        for r in results:
            if r.details:
                err.append([run, r.check.check_id, r.check.name])
                for row in r.details:
                    err.append(["", "", ""] + row)
    for sheet in wb.worksheets:
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = min(60, max(12, max(len(str(c.value or "")) for c in col) + 2))
    wb.save(path)
