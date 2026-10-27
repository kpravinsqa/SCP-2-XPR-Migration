-- =====================================================================
-- SOURCE: legacy "SCP Classic" planning schema (synthetic re-creation)
-- =====================================================================
CREATE TABLE scp_item (
    item_code      TEXT PRIMARY KEY,          -- free text, inconsistent case / dashes / spaces
    item_desc      TEXT,
    uom            TEXT NOT NULL,             -- 'CS' (case) or 'EA' (each)
    case_pack      INTEGER,                   -- units per case
    unit_price     REAL,
    active_flag    TEXT NOT NULL              -- 'Y' / 'N'
);

CREATE TABLE scp_location (
    loc_code       TEXT PRIMARY KEY,          -- legacy codes e.g. 'STHLM'
    loc_name       TEXT,
    country        TEXT
);

CREATE TABLE scp_customer (
    cust_code      TEXT PRIMARY KEY,
    cust_name      TEXT,
    channel        TEXT
);

CREATE TABLE scp_forecast (
    fc_id          INTEGER PRIMARY KEY,
    item_code      TEXT,
    loc_code       TEXT,
    cust_code      TEXT,
    period         TEXT,                      -- 'YYYYMM'
    fc_qty         REAL,                      -- in item UOM
    updated_at     TEXT
);

CREATE TABLE scp_item_param (
    item_code      TEXT,
    loc_code       TEXT,
    lead_time      INTEGER,
    moq            INTEGER,
    ss_days        INTEGER,
    PRIMARY KEY (item_code, loc_code)
);

CREATE TABLE scp_user (
    user_id        INTEGER PRIMARY KEY,
    login          TEXT,
    email          TEXT,
    full_name      TEXT,
    is_active      TEXT                       -- 'Y' / 'N'
);
