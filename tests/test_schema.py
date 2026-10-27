import pytest

EXPECTED_TABLES = {
    "dim_product": {"product_id", "description", "base_uom", "case_pack", "unit_price", "is_active", "source_code"},
    "dim_site": {"site_id", "site_name", "country_iso2"},
    "dim_customer": {"customer_id", "customer_name", "channel"},
    "fact_demand_forecast": {"forecast_key", "product_id", "site_id", "customer_id", "period_start", "qty_each", "source_fc_id"},
    "planning_policy": {"product_id", "site_id", "lead_time_days", "moq_each", "safety_stock_days"},
    "app_user": {"user_id", "username", "email", "display_name", "is_active"},
    "migration_reject": {"reject_id", "source_table", "source_key", "reason_code", "detail"},
}


@pytest.mark.schema
@pytest.mark.smoke
@pytest.mark.parametrize("table, columns", EXPECTED_TABLES.items(), ids=list(EXPECTED_TABLES))
def test_table_and_columns_exist(q, table, columns):
    actual = {r["name"] for r in q(f"PRAGMA table_info({table})")}
    assert actual == columns, f"{table}: missing {columns - actual}, unexpected {actual - columns}"


@pytest.mark.schema
@pytest.mark.parametrize("table, pk", [
    ("dim_product", ["product_id"]), ("dim_site", ["site_id"]), ("dim_customer", ["customer_id"]),
    ("planning_policy", ["product_id", "site_id"]), ("app_user", ["user_id"]),
])
def test_primary_keys(q, table, pk):
    cols = sorted((r["pk"], r["name"]) for r in q(f"PRAGMA table_info({table})") if r["pk"])
    assert [c for _, c in cols] == pk


@pytest.mark.schema
def test_fact_foreign_keys_declared(q):
    fks = {(r["from"], r["table"]) for r in q("PRAGMA foreign_key_list(fact_demand_forecast)")}
    assert fks == {("product_id", "dim_product"), ("site_id", "dim_site"), ("customer_id", "dim_customer")}


@pytest.mark.schema
def test_reporting_index_exists(q):
    names = {r["name"] for r in q("PRAGMA index_list(fact_demand_forecast)")}
    assert "ix_fact_product_period" in names


@pytest.mark.schema
@pytest.mark.parametrize("table, column", [
    ("fact_demand_forecast", "qty_each"), ("fact_demand_forecast", "period_start"),
    ("dim_product", "unit_price"), ("app_user", "email"),
])
def test_not_null_columns(q, table, column):
    info = {r["name"]: r for r in q(f"PRAGMA table_info({table})")}
    assert info[column]["notnull"] == 1
