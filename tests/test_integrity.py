import pytest


@pytest.mark.integrity
@pytest.mark.smoke
def test_sqlite_foreign_key_check_clean(q):
    assert q("PRAGMA foreign_key_check") == []


@pytest.mark.integrity
@pytest.mark.parametrize("table, key", [
    ("dim_product", "product_id"), ("dim_site", "site_id"), ("dim_customer", "customer_id"),
    ("app_user", "email"), ("app_user", "username"), ("fact_demand_forecast", "source_fc_id"),
])
def test_unique_keys(q, table, key):
    assert q.one(f"SELECT COUNT(*) - COUNT(DISTINCT {key}) FROM {table}") == 0


@pytest.mark.integrity
def test_policy_only_for_migrated_products(q):
    assert q.one("SELECT COUNT(*) FROM planning_policy WHERE product_id NOT IN (SELECT product_id FROM dim_product)") == 0


@pytest.mark.integrity
def test_no_negative_or_null_quantities(q):
    assert q.one("SELECT COUNT(*) FROM fact_demand_forecast WHERE qty_each IS NULL OR qty_each < 0") == 0


@pytest.mark.integrity
def test_period_start_is_first_of_month(q):
    assert q.one("SELECT COUNT(*) FROM fact_demand_forecast WHERE strftime('%d', period_start) <> '01' "
                 "OR date(period_start) IS NULL") == 0


@pytest.mark.integrity
def test_migration_run_logged_as_success(q):
    run = q("SELECT status, finished_at FROM migration_run ORDER BY run_id DESC LIMIT 1")[0]
    assert run["status"] == "SUCCESS" and run["finished_at"]
