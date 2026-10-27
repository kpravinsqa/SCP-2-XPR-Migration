"""
SCP Classic -> Xpression NextGen migration (reference ETL).

The rules implemented here are documented in docs/mapping_spec.md. The test
suite does NOT import this module's logic; it re-derives expectations from the
source with independent SQL, as a migration tester would.
"""
from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOCATION_MAP = {"STHLM": "STO", "GBG": "GOT", "OSLO": "OSL", "CPH": "CPH", "HEL": "HEL"}
COUNTRY_MAP = {"Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Finland": "FI"}

# Set INJECT_DEFECTS=1 to run a deliberately broken migration and watch the test suite catch it.
DEFECTS = os.getenv("INJECT_DEFECTS") == "1"
if DEFECTS:
    COUNTRY_MAP = {**COUNTRY_MAP, "Denmark": "DE"}                     # D1: wrong ISO code


def norm_item(code: str) -> str:
    return re.sub(r"[\s\-]", "", code or "").upper()


def run(source: Path, target: Path) -> Path:
    if target.exists():
        target.unlink()
    tgt = sqlite3.connect(target)
    tgt.executescript((ROOT / "sql" / "target_schema.sql").read_text())
    tgt.execute("ATTACH DATABASE ? AS src", (str(source),))
    run_id = tgt.execute("INSERT INTO migration_run(started_at, status) VALUES (?, 'RUNNING')",
                         (datetime.now().isoformat(timespec="seconds"),)).lastrowid

    def reject(table, key, code, detail=""):
        tgt.execute("INSERT INTO migration_reject(source_table, source_key, reason_code, detail) VALUES (?,?,?,?)",
                    (table, str(key), code, detail))

    # ---- products ---------------------------------------------------------
    packs = {}
    for code, desc, uom, pack, price, active in tgt.execute("SELECT * FROM src.scp_item").fetchall():
        if price is None:
            reject("scp_item", code, "MISSING_PRICE")
            continue
        pack = pack or 1
        packs[code] = pack if uom == "CS" else 1
        tgt.execute("INSERT INTO dim_product VALUES (?,?,?,?,?,?,?)",
                    (norm_item(code), desc.strip(), "EA", pack, price, 1 if active == "Y" else 0, code))

    # ---- sites / customers ------------------------------------------------
    for code, name, country in tgt.execute("SELECT * FROM src.scp_location").fetchall():
        tgt.execute("INSERT INTO dim_site VALUES (?,?,?)", (LOCATION_MAP[code], name.strip(), COUNTRY_MAP[country]))
    for code, name, channel in tgt.execute("SELECT * FROM src.scp_customer").fetchall():
        name = name if DEFECTS else name.strip()                                # D2: names not trimmed
        tgt.execute("INSERT INTO dim_customer VALUES (?,?,?)", (code.strip().upper(), name, channel or "UNASSIGNED"))

    customers = {r[0] for r in tgt.execute("SELECT customer_id FROM dim_customer")}
    rejected_items = {r[0] for r in tgt.execute(
        "SELECT source_key FROM migration_reject WHERE source_table='scp_item'")}

    # ---- forecast ---------------------------------------------------------
    rows = tgt.execute("SELECT fc_id, item_code, loc_code, cust_code, period, fc_qty, updated_at "
                       "FROM src.scp_forecast ORDER BY updated_at " + ("ASC" if DEFECTS else "DESC")   # D3: oldest wins
                       + ", fc_id DESC").fetchall()
    seen = set()
    for fc_id, item, loc, cust, period, qty, _ in rows:
        if item in rejected_items:
            reject("scp_forecast", fc_id, "PARENT_REJECTED", f"item {item}")
            continue
        if item not in packs:
            reject("scp_forecast", fc_id, "UNKNOWN_ITEM", item)
            continue
        if loc not in LOCATION_MAP:
            reject("scp_forecast", fc_id, "UNKNOWN_LOCATION", loc)
            continue
        if cust not in customers:
            reject("scp_forecast", fc_id, "UNKNOWN_CUSTOMER", cust)
            continue
        if not period or not re.fullmatch(r"\d{4}(0[1-9]|1[0-2])", period):
            reject("scp_forecast", fc_id, "INVALID_PERIOD", str(period))
            continue
        if qty is None or qty < 0:
            reject("scp_forecast", fc_id, "NEGATIVE_QTY", str(qty))
            continue
        natural = (norm_item(item), LOCATION_MAP[loc], cust, period)
        if natural in seen:
            reject("scp_forecast", fc_id, "SUPERSEDED_DUPLICATE")
            continue
        seen.add(natural)
        qty_each = int(round(qty * packs[item] + 1e-9))
        if DEFECTS and period == "202612":
            continue                                                            # D5: silently drops December
        tgt.execute("INSERT INTO fact_demand_forecast(product_id, site_id, customer_id, period_start, qty_each, source_fc_id) "
                    "VALUES (?,?,?,?,?,?)", (natural[0], natural[1], cust, f"{period[:4]}-{period[4:]}-01", qty_each, fc_id))

    # ---- planning policy --------------------------------------------------
    for item, loc, lt, moq, ss in tgt.execute("SELECT * FROM src.scp_item_param").fetchall():
        key = f"{item}|{loc}"
        if item in rejected_items:
            reject("scp_item_param", key, "PARENT_REJECTED")
        elif not 1 <= lt <= 365:
            reject("scp_item_param", key, "INVALID_LEAD_TIME", str(lt))
        elif not 0 <= ss <= 90:
            reject("scp_item_param", key, "INVALID_SS_DAYS", str(ss))
        else:
            tgt.execute("INSERT INTO planning_policy VALUES (?,?,?,?,?)",
                        (norm_item(item), LOCATION_MAP[loc], lt, moq if DEFECTS else moq * packs[item], ss))  # D4

    # ---- users ------------------------------------------------------------
    emails = set()
    for uid, login, email, name, active in tgt.execute("SELECT * FROM src.scp_user ORDER BY user_id").fetchall():
        if not email:
            reject("scp_user", uid, "MISSING_EMAIL")
            continue
        if email.lower() in emails:
            reject("scp_user", uid, "DUPLICATE_EMAIL", email.lower())
            continue
        emails.add(email.lower())
        tgt.execute("INSERT INTO app_user VALUES (?,?,?,?,?)",
                    (uid, login.lower(), email.lower(), name.strip(), 1 if active == "Y" else 0))

    tgt.execute("UPDATE migration_run SET finished_at=?, status='SUCCESS' WHERE run_id=?",
                (datetime.now().isoformat(timespec="seconds"), run_id))
    tgt.commit()
    tgt.execute("DETACH DATABASE src")
    tgt.close()
    return target


if __name__ == "__main__":
    from etl.seed_source import build

    src = build(ROOT / "db" / "scp_classic.db")
    print("Target DB created at", run(src, ROOT / "db" / "xpr_nextgen.db"))
