"""Builds a deterministic source extract and a target table with known, injected defects."""
import sqlite3
from datetime import date, timedelta

STATUSES = ["NEW", "SHIPPED", "DELIVERED", "CANCELLED"]

# Defects injected into the target. Tests assert the engine finds exactly these.
INJECTED = {
    "missing_records": [1010, 1020, 1030],
    "extra_records": [2001],
    "duplicated": [1040, 1050],
    "null_customer": [1060, 1061],
    "null_amount": [1070],
    "amount_changed": [1080, 1081],
    "amount_as_text": [1090],
    "bad_date_format": [1095],
    "bad_status": [1100],
}


def build(conn: sqlite3.Connection, inject_defects: bool = True) -> None:
    conn.executescript("""
        DROP TABLE IF EXISTS src_orders; DROP TABLE IF EXISTS tgt_orders;
        CREATE TABLE src_orders (order_id INTEGER, customer_id INTEGER, order_date TEXT, amount REAL, status TEXT);
        CREATE TABLE tgt_orders (order_id, customer_id, order_date, amount, status);  -- untyped: keeps bad values
    """)
    start = date(2026, 1, 1)
    rows = [(1000 + i, (i % 20) + 1, (start + timedelta(days=i % 90)).isoformat(),
             round(10 + (i * 37 % 490) + 0.5, 2), STATUSES[i % 4]) for i in range(1, 101)]
    conn.executemany("INSERT INTO src_orders VALUES (?,?,?,?,?)", rows)
    conn.executemany("INSERT INTO tgt_orders VALUES (?,?,?,?,?)", rows)
    if inject_defects:
        d = INJECTED
        q = lambda sql, *a: conn.execute(sql, a)
        for oid in d["missing_records"]:
            q("DELETE FROM tgt_orders WHERE order_id=?", oid)
        q("INSERT INTO tgt_orders VALUES (2001, 5, '2026-02-01', 99.99, 'NEW')")
        for oid in d["duplicated"]:
            q("INSERT INTO tgt_orders SELECT * FROM tgt_orders WHERE order_id=?", oid)
        for oid in d["null_customer"]:
            q("UPDATE tgt_orders SET customer_id=NULL WHERE order_id=?", oid)
        q("UPDATE tgt_orders SET amount=NULL WHERE order_id=?", d["null_amount"][0])
        q("UPDATE tgt_orders SET amount=amount+5 WHERE order_id=?", d["amount_changed"][0])
        q("UPDATE tgt_orders SET amount=amount*2 WHERE order_id=?", d["amount_changed"][1])
        q("UPDATE tgt_orders SET amount='12O.50' WHERE order_id=?", d["amount_as_text"][0])
        q("UPDATE tgt_orders SET order_date='31/01/2026' WHERE order_id=?", d["bad_date_format"][0])
        q("UPDATE tgt_orders SET status='UNKNOWN' WHERE order_id=?", d["bad_status"][0])
    conn.commit()
