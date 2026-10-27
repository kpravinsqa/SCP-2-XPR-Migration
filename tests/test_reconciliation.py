import hashlib

import pytest

ACCEPTED_SOURCE = """
    SELECT s.fc_id, UPPER(REPLACE(REPLACE(s.item_code,'-',''),' ','')) AS product_id, s.period,
           CAST(ROUND(s.fc_qty * CASE WHEN i.uom = 'CS' THEN i.case_pack ELSE 1 END + 1e-9) AS INTEGER) AS qty_each
    FROM src.scp_forecast s JOIN src.scp_item i ON i.item_code = s.item_code
    WHERE s.fc_id IN (SELECT source_fc_id FROM fact_demand_forecast)
"""


@pytest.mark.reconciliation
@pytest.mark.smoke
def test_grand_total_quantity(q):
    src = q.one(f"SELECT SUM(qty_each) FROM ({ACCEPTED_SOURCE})")
    tgt = q.one("SELECT SUM(qty_each) FROM fact_demand_forecast")
    assert src == tgt


@pytest.mark.reconciliation
def test_quantity_by_product(q):
    src = {r["product_id"]: r["qty"] for r in q(f"SELECT product_id, SUM(qty_each) qty FROM ({ACCEPTED_SOURCE}) GROUP BY 1")}
    tgt = {r["product_id"]: r["qty"] for r in q("SELECT product_id, SUM(qty_each) qty FROM fact_demand_forecast GROUP BY 1")}
    assert src == tgt


@pytest.mark.reconciliation
def test_quantity_by_month(q):
    src = {r["p"]: r["qty"] for r in q(f"SELECT substr(period,1,4)||'-'||substr(period,5,2)||'-01' p, SUM(qty_each) qty FROM ({ACCEPTED_SOURCE}) GROUP BY 1")}
    tgt = {r["p"]: r["qty"] for r in q("SELECT period_start p, SUM(qty_each) qty FROM fact_demand_forecast GROUP BY 1")}
    assert src == tgt


@pytest.mark.reconciliation
def test_row_level_hash_comparison(q):
    """Canonical-string MD5 per row on both sides: catches any drift that aggregates could mask."""
    def digest(rows):
        h = hashlib.md5()
        for r in rows:
            h.update("|".join(str(v) for v in r.values()).encode())
        return h.hexdigest()

    src = q(f"""SELECT a.fc_id, a.product_id,
                CASE l.loc_code WHEN 'STHLM' THEN 'STO' WHEN 'GBG' THEN 'GOT' WHEN 'OSLO' THEN 'OSL' ELSE l.loc_code END AS site,
                s.cust_code, substr(a.period,1,4)||'-'||substr(a.period,5,2)||'-01' AS period, a.qty_each
                FROM ({ACCEPTED_SOURCE}) a JOIN src.scp_forecast s ON s.fc_id = a.fc_id
                JOIN src.scp_location l ON l.loc_code = s.loc_code ORDER BY a.fc_id""")
    tgt = q("""SELECT source_fc_id, product_id, site_id, customer_id, period_start, qty_each
               FROM fact_demand_forecast ORDER BY source_fc_id""")
    assert digest(src) == digest(tgt)


@pytest.mark.reconciliation
def test_inventory_value_reconciles(q):
    src = q.one(f"""SELECT ROUND(SUM(a.qty_each * i.unit_price), 2) FROM ({ACCEPTED_SOURCE}) a
                    JOIN src.scp_forecast s ON s.fc_id = a.fc_id JOIN src.scp_item i ON i.item_code = s.item_code""")
    tgt = q.one("""SELECT ROUND(SUM(f.qty_each * p.unit_price), 2) FROM fact_demand_forecast f
                   JOIN dim_product p ON p.product_id = f.product_id""")
    assert src == tgt
