import pytest


@pytest.mark.completeness
@pytest.mark.smoke
@pytest.mark.parametrize("source, target, reject_table", [
    ("scp_item", "dim_product", "scp_item"),
    ("scp_location", "dim_site", None),
    ("scp_customer", "dim_customer", None),
    ("scp_forecast", "fact_demand_forecast", "scp_forecast"),
    ("scp_item_param", "planning_policy", "scp_item_param"),
    ("scp_user", "app_user", "scp_user"),
])
def test_source_count_equals_target_plus_rejects(q, source, target, reject_table):
    src = q.one(f"SELECT COUNT(*) FROM src.{source}")
    tgt = q.one(f"SELECT COUNT(*) FROM {target}")
    rej = q.one("SELECT COUNT(*) FROM migration_reject WHERE source_table = ?", (reject_table,)) if reject_table else 0
    assert src == tgt + rej, f"{source}: source={src}, target={tgt}, rejected={rej}"


@pytest.mark.completeness
def test_expected_forecast_volume(q):
    """Independent derivation of how many rows *should* land, from the source alone."""
    expected = q.one("""
        WITH valid AS (
          SELECT s.*, ROW_NUMBER() OVER (
                   PARTITION BY UPPER(REPLACE(REPLACE(s.item_code,'-',''),' ','')), s.loc_code, s.cust_code, s.period
                   ORDER BY s.updated_at DESC, s.fc_id DESC) AS rn
          FROM src.scp_forecast s
          JOIN src.scp_item i     ON i.item_code = s.item_code AND i.unit_price IS NOT NULL
          JOIN src.scp_location l ON l.loc_code = s.loc_code
          JOIN src.scp_customer c ON c.cust_code = s.cust_code
          WHERE s.period GLOB '[0-9][0-9][0-9][0-9][0-1][0-9]' AND CAST(substr(s.period,5,2) AS INT) BETWEEN 1 AND 12
            AND s.fc_qty >= 0)
        SELECT COUNT(*) FROM valid WHERE rn = 1""")
    assert q.one("SELECT COUNT(*) FROM fact_demand_forecast") == expected


@pytest.mark.completeness
@pytest.mark.parametrize("period", ["2026-07-01", "2026-09-01", "2026-12-01", "2027-03-01", "2027-06-01"])
def test_every_period_is_populated(q, period):
    combos = q.one("SELECT COUNT(DISTINCT product_id || site_id || customer_id) FROM fact_demand_forecast")
    in_period = q.one("SELECT COUNT(*) FROM fact_demand_forecast WHERE period_start = ?", (period,))
    assert in_period == combos, f"{period} has {in_period} rows, expected {combos}"


@pytest.mark.completeness
def test_all_twelve_months_migrated(q):
    assert q.one("SELECT COUNT(DISTINCT period_start) FROM fact_demand_forecast") == 12


@pytest.mark.completeness
def test_no_target_rows_without_source(q):
    assert q.one("""SELECT COUNT(*) FROM fact_demand_forecast f
                    LEFT JOIN src.scp_forecast s ON s.fc_id = f.source_fc_id WHERE s.fc_id IS NULL""") == 0
