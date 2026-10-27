"""
Generate a deterministic, synthetic SCP Classic source database.

Includes deliberately "dirty" legacy records (mixed-case codes, trailing
spaces, negative quantities, orphans, duplicates, invalid periods) so the
migration's cleansing and reject rules can be tested.
"""
from __future__ import annotations

import random
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ITEMS = [
    # item_code (raw legacy), desc, uom, case_pack, price, active
    ("p-100 ", "Rye Crispbread 250g", "CS", 12, 1.85, "Y"),
    ("P-200", "Lingonberry Jam 400g", "CS", 6, 3.40, "Y"),
    ("p300", "Oat Drink Barista 1L", "CS", 8, 2.10, "Y"),
    ("P-400", "Pickled Herring 500g", "EA", None, 4.95, "Y"),
    ("P 500", "Cloudberry Preserve 300g", "EA", 1, 6.80, "Y"),
    ("P-600", "Crispbread Sesame 200g", "CS", 12, 1.95, "N"),
    ("P-700", "Cardamom Buns 6pk", "CS", 4, 3.25, "Y"),
    ("P-800", "Smoked Salmon 200g", "EA", 1, None, "Y"),      # missing price -> rejected
]
LOCATIONS = [("STHLM", "Stockholm DC", "Sweden"), ("GBG", "Gothenburg DC", "Sweden"),
             ("OSLO", "Oslo DC", "Norway"), ("CPH", "Copenhagen DC", "Denmark"), ("HEL", "Helsinki DC", "Finland")]
CUSTOMERS = [("ICA", "  ICA Gruppen ", "Retail"), ("COOP", "Coop Sverige", "Retail"), ("AXF", "Axfood", "Retail"),
             ("REMA", "Rema 1000", "Discount"), ("KESKO", "Kesko Oyj", None), ("SALL", "Salling Group", "Retail")]
PERIODS = [f"2026{m:02d}" for m in range(7, 13)] + [f"2027{m:02d}" for m in range(1, 7)]   # 12 months


def build(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript((ROOT / "sql" / "source_schema.sql").read_text())
    rnd = random.Random(42)

    con.executemany("INSERT INTO scp_item VALUES (?,?,?,?,?,?)", ITEMS)
    con.executemany("INSERT INTO scp_location VALUES (?,?,?)", LOCATIONS)
    con.executemany("INSERT INTO scp_customer VALUES (?,?,?)", CUSTOMERS)

    fc_id = 1
    rows = []
    for item in ITEMS:
        for loc in LOCATIONS[:3] if item[2] == "EA" else LOCATIONS:
            for cust in CUSTOMERS[:4]:
                for period in PERIODS:
                    qty = round(rnd.uniform(5, 120), 1) if item[2] == "CS" else rnd.randint(20, 900)
                    rows.append((fc_id, item[0], loc[0], cust[0], period, qty, "2026-06-01 10:00:00"))
                    fc_id += 1
    # ---- dirty records ---------------------------------------------------
    dirty = [
        (900001, "P-200", "STHLM", "ICA", "202607", -15.0, "2026-06-02 09:00:00"),     # negative qty
        (900002, "P-200", "GBG", "COOP", "202608", -1.0, "2026-06-02 09:00:00"),       # negative qty
        (900003, "P-999", "STHLM", "ICA", "202607", 10.0, "2026-06-02 09:00:00"),      # unknown item
        (900004, "P-700", "MALMO", "ICA", "202607", 10.0, "2026-06-02 09:00:00"),      # unknown location
        (900005, "P-700", "STHLM", "NOPE", "202607", 10.0, "2026-06-02 09:00:00"),     # unknown customer
        (900006, "P-700", "STHLM", "ICA", None, 10.0, "2026-06-02 09:00:00"),          # null period
        (900007, "P-700", "STHLM", "ICA", "202613", 10.0, "2026-06-02 09:00:00"),      # invalid month
        # duplicate of an existing PLC-period, NEWER -> must win
        (900008, "p-100 ", "STHLM", "ICA", "202607", 99.0, "2026-06-15 08:00:00"),
        # duplicate of an existing PLC-period, OLDER -> must be rejected
        (900009, "P-200", "OSLO", "AXF", "202609", 1.0, "2025-12-31 23:59:59"),
    ]
    con.executemany("INSERT INTO scp_forecast VALUES (?,?,?,?,?,?,?)", rows + dirty)

    params = []
    for item in ITEMS:
        for loc in LOCATIONS:
            params.append((item[0], loc[0], rnd.randint(3, 45), rnd.randint(1, 20), rnd.randint(0, 21)))
    params[3] = (params[3][0], params[3][1], 0, params[3][3], params[3][4])       # lead time 0 -> reject
    params[7] = (params[7][0], params[7][1], 10, params[7][3], 120)               # ss days 120 -> reject
    con.executemany("INSERT INTO scp_item_param VALUES (?,?,?,?,?)", params)

    users = [(1, "anna.berg", "Anna.Berg@Example.com", "Anna Berg", "Y"),
             (2, "lars.n", "lars.nilsson@example.com", "Lars Nilsson", "Y"),
             (3, "LARS.N2", "LARS.NILSSON@EXAMPLE.COM", "Lars Nilsson", "N"),   # duplicate email (case) -> reject
             (4, "mette.h", "mette.hansen@example.com", " Mette Hansen ", "N"),
             (5, "jukka.v", None, "Jukka Virtanen", "Y")]                       # missing email -> reject
    con.executemany("INSERT INTO scp_user VALUES (?,?,?,?,?)", users)
    con.commit()
    con.close()
    return path


if __name__ == "__main__":
    print("Source DB created at", build(ROOT / "db" / "scp_classic.db"))
