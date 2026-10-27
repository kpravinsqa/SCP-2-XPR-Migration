"""
Builds the synthetic source DB, runs the migration into a fresh target DB and
exposes a connection to the TARGET with the SOURCE attached as schema ``src``,
so tests can write cross-database reconciliation SQL.
"""
import sqlite3

import pytest

from etl.migrate import run
from etl.seed_source import build


@pytest.fixture(scope="session")
def databases(tmp_path_factory):
    work = tmp_path_factory.mktemp("db")
    source = build(work / "scp_classic.db")
    target = run(source, work / "xpr_nextgen.db")
    return source, target


@pytest.fixture(scope="session")
def db(databases):
    source, target = databases
    con = sqlite3.connect(target)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("ATTACH DATABASE ? AS src", (str(source),))
    yield con
    con.close()


def scalar(con, sql, params=()):
    return con.execute(sql, params).fetchone()[0]


@pytest.fixture(scope="session")
def q(db):
    """Helper: q(sql) -> list of dict rows; q.one(sql) -> scalar."""
    class Query:
        def __call__(self, sql, params=()):
            return [dict(r) for r in db.execute(sql, params).fetchall()]

        def one(self, sql, params=()):
            return scalar(db, sql, params)

    return Query()
