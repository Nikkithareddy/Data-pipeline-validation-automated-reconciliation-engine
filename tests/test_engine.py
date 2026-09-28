import sqlite3

import pytest

from src import engine, sample_data
from src.sample_data import INJECTED

FILES = ("validation_checks.sql", "reconciliation_checks.sql")


@pytest.fixture
def checks():
    return engine.load_checks(*FILES)


def build(defects=True):
    conn = sqlite3.connect(":memory:")
    sample_data.build(conn, inject_defects=defects)
    return conn


def actuals(conn, checks):
    return {r.check.check_id: r.actual for r in engine.run_checks(conn, checks)}


def test_all_checks_loaded(checks):
    assert len(checks) == 15
    assert len({c.check_id for c in checks}) == 15


def test_clean_data_passes_every_check(checks):
    results = engine.run_checks(build(defects=False), checks)
    assert all(r.passed for r in results), [r.check.check_id for r in results if not r.passed]


def test_engine_finds_exactly_the_injected_defects(checks):
    a = actuals(build(), checks)
    assert a["V02"] == len(INJECTED["missing_records"])
    assert a["V03"] == len(INJECTED["extra_records"])
    assert a["V04"] == len(INJECTED["null_customer"])
    assert a["V05"] == len(INJECTED["null_amount"])
    assert a["V07"] == len(INJECTED["duplicated"])
    assert a["V08"] == len(INJECTED["amount_as_text"])
    assert a["V09"] == len(INJECTED["bad_date_format"])
    assert a["V10"] == len(INJECTED["bad_status"])
    assert a["V06"] == 0 and a["V11"] == 0            # nothing injected -> no false positives
    assert a["R02"] == len(INJECTED["amount_changed"]) + len(INJECTED["amount_as_text"])


def test_reconciliation_flags_totals(checks):
    a = actuals(build(), checks)
    assert a["R01"] > 0 and a["R03"] > 0 and a["R04"] > 0
    assert a["V01"] == 3 - 1 - 2                      # 3 missing, +1 extra, +2 duplicates -> net 0
    assert a["V01"] == 0                              # equal counts hide the defects: why we check more than counts


def test_failed_checks_capture_offending_rows(checks):
    results = {r.check.check_id: r for r in engine.run_checks(build(), checks)}
    missing_ids = [row[0] for row in results["V02"].details[1:]]
    assert missing_ids == INJECTED["missing_records"]


def test_cleanup_fixes_everything(checks):
    conn = build()
    engine.apply_cleanup(conn)
    results = engine.run_checks(conn, checks)
    assert all(r.passed for r in results), [r.check.check_id for r in results if not r.passed]
