import pytest


@pytest.mark.rejects
@pytest.mark.parametrize("table, key, reason", [
    ("scp_forecast", "900001", "NEGATIVE_QTY"),
    ("scp_forecast", "900002", "NEGATIVE_QTY"),
    ("scp_forecast", "900003", "UNKNOWN_ITEM"),
    ("scp_forecast", "900004", "UNKNOWN_LOCATION"),
    ("scp_forecast", "900005", "UNKNOWN_CUSTOMER"),
    ("scp_forecast", "900006", "INVALID_PERIOD"),
    ("scp_forecast", "900007", "INVALID_PERIOD"),
    ("scp_forecast", "900009", "SUPERSEDED_DUPLICATE"),
    ("scp_item", "P-800", "MISSING_PRICE"),
    ("scp_user", "3", "DUPLICATE_EMAIL"),
    ("scp_user", "5", "MISSING_EMAIL"),
])
def test_dirty_record_rejected_with_reason(q, table, key, reason):
    assert q.one("SELECT reason_code FROM migration_reject WHERE source_table = ? AND source_key = ?", (table, key)) == reason


@pytest.mark.rejects
def test_newer_duplicate_wins(q):
    """fc 900008 (updated later) supersedes the original row for P100/STHLM/ICA/202607."""
    assert q.one("SELECT qty_each FROM fact_demand_forecast WHERE source_fc_id = 900008") == 99 * 12
    original = q.one("""SELECT fc_id FROM src.scp_forecast WHERE item_code = 'p-100 ' AND loc_code = 'STHLM'
                        AND cust_code = 'ICA' AND period = '202607' AND fc_id <> 900008""")
    assert q.one("SELECT reason_code FROM migration_reject WHERE source_key = ?", (str(original),)) == "SUPERSEDED_DUPLICATE"


@pytest.mark.rejects
def test_children_of_rejected_item_cascade(q):
    children = q.one("SELECT COUNT(*) FROM src.scp_forecast WHERE item_code = 'P-800'")
    rejected = q.one("SELECT COUNT(*) FROM migration_reject WHERE source_table = 'scp_forecast' AND reason_code = 'PARENT_REJECTED'")
    assert children == rejected > 0
    assert q.one("SELECT COUNT(*) FROM fact_demand_forecast WHERE product_id = 'P800'") == 0


@pytest.mark.rejects
@pytest.mark.parametrize("reason", ["INVALID_LEAD_TIME", "INVALID_SS_DAYS"])
def test_invalid_planning_parameters_rejected(q, reason):
    assert q.one("SELECT COUNT(*) FROM migration_reject WHERE source_table='scp_item_param' AND reason_code = ?", (reason,)) == 1


@pytest.mark.rejects
def test_reject_rate_within_tolerance(q):
    """Business sign-off rule: excluding cascades, < 1 % of forecast rows may be rejected."""
    total = q.one("SELECT COUNT(*) FROM src.scp_forecast")
    rejected = q.one("SELECT COUNT(*) FROM migration_reject WHERE source_table='scp_forecast' AND reason_code <> 'PARENT_REJECTED'")
    assert rejected / total < 0.01
