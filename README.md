# Data Migration Testing — SCP Classic → Xpression NextGen

![Tests](https://github.com/kpravinsqa/db-testing-scp-to-xpr-migration/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![SQL](https://img.shields.io/badge/SQL-ANSI%20%7C%20SQLite-003B57) ![Pytest](https://img.shields.io/badge/pytest-8.x-0A9EDC)

Database and ETL test framework for migrating a **legacy supply chain planning schema (SCP Classic)** to a
**next-generation platform schema (Xpression NextGen)**, based on the migration validation I did on the
**SCP → XPR migration** project.

> **Confidentiality note:** schemas, data and ETL are **synthetic re-creations** written for this portfolio. No client
> data or proprietary code is included.

## What it demonstrates

* **Source-to-target mapping spec** with 13 transformation rules and 12 reject rules ([docs/mapping_spec.md](docs/mapping_spec.md))
* **Independent expectations**: every check is derived from the *source* with SQL (window functions, anti-joins, CTEs), never by re-running ETL logic
* **6 validation layers**: schema, completeness, accuracy, integrity, reconciliation (aggregate + row-hash), data-quality rejects
* **Reusable SQL library**: `sql/validation/*.sql`, where each query returns offending rows (0 rows = pass), runnable in any SQL client
* **Dirty legacy data on purpose**: mixed-case codes, trailing spaces, negative quantities, orphans, invalid periods, newer/older duplicates, cascading parent rejects
* **Proof the tests work**: `INJECT_DEFECTS=1` runs a broken ETL with 5 seeded bugs, and the suite catches all 5 (11 failing checks). CI asserts this on every push.
* **Sign-off artefact**: an Excel reconciliation workbook (summary, validation SQL, reject summary/detail, qty by product)

## Quick start

```bash
git clone https://github.com/kpravinsqa/db-testing-scp-to-xpr-migration.git
cd db-testing-scp-to-xpr-migration
pip install -r requirements.txt

pytest                                   # 94 checks, HTML report in reports/
pytest -m reconciliation                 # one layer only
INJECT_DEFECTS=1 pytest                  # watch the suite catch the seeded ETL defects
python -m reports_tool.recon_report      # reports/migration_recon_report.xlsx
python -m etl.migrate                    # build db/scp_classic.db + db/xpr_nextgen.db to explore in DBeaver
```

## Structure

```
sql/source_schema.sql        legacy schema          sql/target_schema.sql   new schema + reject/run log
sql/validation/*.sql         10 zero-row validation queries
etl/seed_source.py           deterministic synthetic source incl. dirty records
etl/migrate.py               reference ETL (+ INJECT_DEFECTS switch)
tests/                       schema · completeness · accuracy · integrity · reconciliation · rejects
reports_tool/recon_report.py Excel sign-off workbook
docs/                        mapping spec, test strategy
```

## Sample results

| Entity | Source | Target | Rejected | Status |
|---|---:|---:|---:|---|
| Items → dim_product | 8 | 7 | 1 | PASS |
| Forecast → fact_demand_forecast | 1,641 | 1,488 | 153 | PASS |
| Item params → planning_policy | 40 | 33 | 7 | PASS |
| Users → app_user | 5 | 3 | 2 | PASS |

## Author

**Pravin Khedkar**, QA Lead / SDET · [@kpravinsqa](https://github.com/kpravinsqa)
