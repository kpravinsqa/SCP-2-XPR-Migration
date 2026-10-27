import pytest


@pytest.mark.accuracy
@pytest.mark.parametrize("legacy, site, iso", [("STHLM", "STO", "SE"), ("GBG", "GOT", "SE"), ("OSLO", "OSL", "NO"),
                                               ("CPH", "CPH", "DK"), ("HEL", "HEL", "FI")])
def test_location_mapping(q, legacy, site, iso):
    row = q("SELECT site_id, country_iso2, site_name FROM dim_site WHERE site_id = ?", (site,))[0]
    src = q("SELECT loc_name FROM src.scp_location WHERE loc_code = ?", (legacy,))[0]
    assert row == {"site_id": site, "country_iso2": iso, "site_name": src["loc_name"].strip()}


@pytest.mark.accuracy
@pytest.mark.parametrize("raw, normalised", [("p-100 ", "P100"), ("P-200", "P200"), ("p300", "P300"), ("P 500", "P500")])
def test_item_code_normalisation(q, raw, normalised):
    assert q.one("SELECT product_id FROM dim_product WHERE source_code = ?", (raw,)) == normalised


@pytest.mark.accuracy
def test_active_flag_converted_to_boolean(q):
    rows = q("""SELECT p.is_active, i.active_flag FROM dim_product p JOIN src.scp_item i ON i.item_code = p.source_code""")
    assert all(r["is_active"] == (1 if r["active_flag"] == "Y" else 0) for r in rows)
    assert q.one("SELECT is_active FROM dim_product WHERE product_id = 'P600'") == 0


@pytest.mark.accuracy
def test_missing_case_pack_defaults_to_one(q):
    assert q.one("SELECT case_pack FROM dim_product WHERE product_id = 'P400'") == 1


@pytest.mark.accuracy
def test_base_uom_is_each_everywhere(q):
    assert q.one("SELECT COUNT(*) FROM dim_product WHERE base_uom <> 'EA'") == 0


@pytest.mark.accuracy
def test_customer_name_trimmed_and_channel_defaulted(q):
    assert q.one("SELECT customer_name FROM dim_customer WHERE customer_id = 'ICA'") == "ICA Gruppen"
    assert q.one("SELECT channel FROM dim_customer WHERE customer_id = 'KESKO'") == "UNASSIGNED"


@pytest.mark.accuracy
@pytest.mark.parametrize("fc_id", [1, 2, 13, 500, 1000])
def test_spot_check_forecast_rows(q, fc_id):
    src = q("""SELECT s.fc_qty, i.uom, COALESCE(i.case_pack,1) AS pack, s.period FROM src.scp_forecast s
               JOIN src.scp_item i ON i.item_code = s.item_code WHERE s.fc_id = ?""", (fc_id,))[0]
    tgt = q("SELECT qty_each, period_start FROM fact_demand_forecast WHERE source_fc_id = ?", (fc_id,))
    if not tgt:                                       # superseded by a newer duplicate
        assert q.one("SELECT reason_code FROM migration_reject WHERE source_key = ?", (str(fc_id),)) == "SUPERSEDED_DUPLICATE"
        return
    factor = src["pack"] if src["uom"] == "CS" else 1
    assert tgt[0]["qty_each"] == round(src["fc_qty"] * factor + 1e-9)
    assert tgt[0]["period_start"] == f"{src['period'][:4]}-{src['period'][4:]}-01"


@pytest.mark.accuracy
def test_user_emails_lowercased_and_flags(q):
    rows = q("SELECT username, email, display_name, is_active FROM app_user ORDER BY user_id")
    assert rows == [
        {"username": "anna.berg", "email": "anna.berg@example.com", "display_name": "Anna Berg", "is_active": 1},
        {"username": "lars.n", "email": "lars.nilsson@example.com", "display_name": "Lars Nilsson", "is_active": 1},
        {"username": "mette.h", "email": "mette.hansen@example.com", "display_name": "Mette Hansen", "is_active": 0},
    ]


@pytest.mark.accuracy
def test_planning_policy_values_carried_over(q):
    rows = q("""SELECT pp.lead_time_days, ip.lead_time, pp.safety_stock_days, ip.ss_days
                FROM planning_policy pp JOIN dim_product p ON p.product_id = pp.product_id
                JOIN src.scp_item_param ip ON ip.item_code = p.source_code
                 AND ip.loc_code = CASE pp.site_id WHEN 'STO' THEN 'STHLM' WHEN 'GOT' THEN 'GBG' WHEN 'OSL' THEN 'OSLO' ELSE pp.site_id END""")
    assert len(rows) == q.one("SELECT COUNT(*) FROM planning_policy")
    assert all(r["lead_time_days"] == r["lead_time"] and r["safety_stock_days"] == r["ss_days"] for r in rows)
