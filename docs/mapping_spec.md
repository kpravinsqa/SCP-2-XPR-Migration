# Source-to-Target Mapping Specification: SCP Classic → Xpression NextGen

All structures and data here are synthetic, re-created for a portfolio.

## Entity mapping

| Source table | Target table | Grain | Load rule |
|---|---|---|---|
| `scp_item` | `dim_product` | 1 row per item | reject if `unit_price` is NULL |
| `scp_location` | `dim_site` | 1 row per DC | full load, code mapping |
| `scp_customer` | `dim_customer` | 1 row per customer | full load |
| `scp_forecast` | `fact_demand_forecast` | product × site × customer × month | cleanse, de-duplicate, reject invalid |
| `scp_item_param` | `planning_policy` | product × site | reject out-of-range values |
| `scp_user` | `app_user` | 1 row per unique email | reject missing / duplicate email |

## Column transformation rules

| # | Target column | Source | Rule |
|---|---|---|---|
| T1 | `dim_product.product_id` | `scp_item.item_code` | `UPPER`, remove spaces and dashes (`'p-100 '` → `P100`) |
| T2 | `dim_product.source_code` | `scp_item.item_code` | copied verbatim (lineage) |
| T3 | `dim_product.case_pack` | `scp_item.case_pack` | NULL → 1 |
| T4 | `dim_product.is_active` | `active_flag` | `'Y'` → 1, `'N'` → 0 |
| T5 | `dim_site.site_id` | `loc_code` | STHLM→STO, GBG→GOT, OSLO→OSL, CPH→CPH, HEL→HEL |
| T6 | `dim_site.country_iso2` | `country` | Sweden→SE, Norway→NO, Denmark→DK, Finland→FI |
| T7 | `dim_customer.customer_name` | `cust_name` | `TRIM` |
| T8 | `dim_customer.channel` | `channel` | NULL → `'UNASSIGNED'` |
| T9 | `fact.period_start` | `period` (`YYYYMM`) | → `YYYY-MM-01` |
| T10 | `fact.qty_each` | `fc_qty` | CS items: `ROUND(fc_qty × case_pack)`; EA items: `ROUND(fc_qty)` |
| T11 | `planning_policy.moq_each` | `moq` | × case_pack for CS items |
| T12 | `app_user.email` / `username` | `email` / `login` | lower-case |
| T13 | `app_user.display_name` | `full_name` | `TRIM` |

## Data-quality / reject rules

| Code | Applies to | Condition |
|---|---|---|
| `MISSING_PRICE` | item | `unit_price IS NULL` |
| `PARENT_REJECTED` | forecast, param | the parent item was rejected (cascade) |
| `UNKNOWN_ITEM` / `UNKNOWN_LOCATION` / `UNKNOWN_CUSTOMER` | forecast | FK not found in master data |
| `INVALID_PERIOD` | forecast | NULL, or not `YYYYMM` with month 01-12 |
| `NEGATIVE_QTY` | forecast | `fc_qty < 0` |
| `SUPERSEDED_DUPLICATE` | forecast | same natural key exists with a later `updated_at` (latest wins) |
| `INVALID_LEAD_TIME` / `INVALID_SS_DAYS` | param | lead time not 1-365 / SS days not 0-90 |
| `MISSING_EMAIL` / `DUPLICATE_EMAIL` | user | email NULL / already loaded (case-insensitive) |

**Sign-off criteria:** source = target + rejects for every entity; all `sql/validation` checks return 0 rows; quantity
and value reconcile at total, product and month level; non-cascade reject rate < 1 %.
