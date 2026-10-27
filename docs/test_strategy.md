# Migration Test Strategy

| Layer | Question answered | Where |
|---|---|---|
| Schema | Does the target DDL match the design (tables, columns, PK/FK, NOT NULL, indexes)? | `tests/test_schema.py` |
| Completeness | Did every source row land or get rejected, with nothing extra and no missing periods? | `tests/test_completeness.py`, `sql/validation/03` |
| Accuracy | Is every transformation rule T1-T13 applied correctly? | `tests/test_accuracy.py`, `sql/validation/05-09` |
| Integrity | Are keys unique, FKs valid and values in range? | `tests/test_integrity.py`, `sql/validation/01-02` |
| Reconciliation | Do totals, product/month aggregates, value and row hashes match? | `tests/test_reconciliation.py` |
| Data quality | Is each dirty record rejected with the right reason; does latest-wins de-duplication work? | `tests/test_rejects.py` |

**Approach:** expectations are derived **independently from the source with SQL**, never by re-using the ETL code, so
a bug in the ETL cannot hide itself.

**Proof the suite works:** `INJECT_DEFECTS=1 pytest` runs a broken migration with 5 seeded defects (wrong ISO code,
untrimmed names, oldest-duplicate-wins, MOQ not converted, December silently dropped). The suite fails 11 checks, and
every seeded defect is caught.

**Portability:** SQL is ANSI-style and runs on SQLite for zero-setup CI. For SQL Server / PostgreSQL / Databricks, swap
`sqlite3` for the matching driver and adjust `GLOB` / `strftime` to `LIKE` / `DATE_TRUNC`.
