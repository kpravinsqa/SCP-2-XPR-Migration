-- =====================================================================
-- TARGET: "Xpression NextGen" planning schema (synthetic re-creation)
-- =====================================================================
PRAGMA foreign_keys = ON;

CREATE TABLE dim_product (
    product_id     TEXT PRIMARY KEY,                 -- normalised: upper, no dash/space
    description    TEXT NOT NULL,
    base_uom       TEXT NOT NULL CHECK (base_uom = 'EA'),
    case_pack      INTEGER NOT NULL CHECK (case_pack >= 1),
    unit_price     NUMERIC(12,4) NOT NULL CHECK (unit_price >= 0),
    is_active      INTEGER NOT NULL CHECK (is_active IN (0,1)),
    source_code    TEXT NOT NULL UNIQUE              -- lineage back to scp_item.item_code
);

CREATE TABLE dim_site (
    site_id        TEXT PRIMARY KEY,
    site_name      TEXT NOT NULL,
    country_iso2   TEXT NOT NULL CHECK (length(country_iso2) = 2)
);

CREATE TABLE dim_customer (
    customer_id    TEXT PRIMARY KEY,
    customer_name  TEXT NOT NULL,
    channel        TEXT NOT NULL
);

CREATE TABLE fact_demand_forecast (
    forecast_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id     TEXT NOT NULL REFERENCES dim_product(product_id),
    site_id        TEXT NOT NULL REFERENCES dim_site(site_id),
    customer_id    TEXT NOT NULL REFERENCES dim_customer(customer_id),
    period_start   DATE NOT NULL,                    -- 'YYYY-MM-01'
    qty_each       INTEGER NOT NULL CHECK (qty_each >= 0),
    source_fc_id   INTEGER NOT NULL UNIQUE,
    UNIQUE (product_id, site_id, customer_id, period_start)
);

CREATE TABLE planning_policy (
    product_id     TEXT NOT NULL REFERENCES dim_product(product_id),
    site_id        TEXT NOT NULL REFERENCES dim_site(site_id),
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days BETWEEN 1 AND 365),
    moq_each       INTEGER NOT NULL CHECK (moq_each >= 1),
    safety_stock_days INTEGER NOT NULL CHECK (safety_stock_days BETWEEN 0 AND 90),
    PRIMARY KEY (product_id, site_id)
);

CREATE TABLE app_user (
    user_id        INTEGER PRIMARY KEY,
    username       TEXT NOT NULL UNIQUE,
    email          TEXT NOT NULL UNIQUE,             -- lower-case
    display_name   TEXT NOT NULL,
    is_active      INTEGER NOT NULL CHECK (is_active IN (0,1))
);

CREATE INDEX ix_fact_product_period ON fact_demand_forecast(product_id, period_start);

-- Every source row that could not be migrated, with the rule that rejected it
CREATE TABLE migration_reject (
    reject_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    source_table   TEXT NOT NULL,
    source_key     TEXT NOT NULL,
    reason_code    TEXT NOT NULL,
    detail         TEXT
);

CREATE TABLE migration_run (
    run_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at     TEXT NOT NULL,
    finished_at    TEXT,
    status         TEXT NOT NULL
);
