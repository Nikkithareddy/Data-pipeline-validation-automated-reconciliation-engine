"""Usage: python run_validation.py [--clean-data] [--no-cleanup]

Builds sample data, runs validation + reconciliation checks, applies cleanup, re-runs the checks to verify
the cleanup, and writes output/execution_tracker.xlsx.
"""
import argparse
import sqlite3

from src import engine, sample_data, tracker

FILES = ("validation_checks.sql", "reconciliation_checks.sql")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean-data", action="store_true", help="build target without injected defects")
    ap.add_argument("--no-cleanup", action="store_true", help="skip the cleanup + verification run")
    args = ap.parse_args()

    conn = sqlite3.connect(":memory:")
    sample_data.build(conn, inject_defects=not args.clean_data)
    checks = engine.load_checks(*FILES)

    runs = {"Before cleanup": engine.run_checks(conn, checks)}
    if not args.no_cleanup:
        engine.apply_cleanup(conn)
        runs["After cleanup"] = engine.run_checks(conn, checks)

    for run, results in runs.items():
        failed = [r for r in results if not r.passed]
        print(f"\n== {run}: {len(results) - len(failed)}/{len(results)} checks passed ==")
        for r in failed:
            print(f"  FAIL {r.check.check_id} [{r.check.category}] {r.check.name}: actual={r.actual}")
    tracker.write_tracker(runs, "output/execution_tracker.xlsx")
    print("\nTracker written to output/execution_tracker.xlsx")


if __name__ == "__main__":
    main()
