"""Runs every file in sql/validation/. Each query returns the offending rows, so 0 rows = PASS."""
from pathlib import Path

import pytest

SQL_DIR = Path(__file__).resolve().parent.parent / "sql" / "validation"
QUERIES = sorted(SQL_DIR.glob("*.sql"))


@pytest.mark.integrity
@pytest.mark.accuracy
@pytest.mark.parametrize("sql_file", QUERIES, ids=[p.stem for p in QUERIES])
def test_validation_query_returns_no_rows(q, sql_file):
    rows = q(sql_file.read_text())
    assert rows == [], f"{sql_file.name} found {len(rows)} offending row(s), e.g. {rows[:3]}"
