"""Test helpers — a scripted fake psycopg AsyncConnection and AMQP client.

`_Pg` answers `cursor()` calls from a queue of canned result sets, records
every query, and counts commits; services under test see real async
context managers, real row objects, and real call order.
"""

import queue
import unittest.mock


class _Result:
    def __init__(self, rows=(), fetchone=None, rowcount=1):
        self._rows = list(rows)
        self._one = fetchone
        self.rowcount = rowcount

    async def fetchone(self):
        if self._one is not None:
            return self._one
        return self._rows.pop(0) if self._rows else None

    async def fetchall(self):
        rows, self._rows = self._rows, []
        return rows


class _Cursor:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, query, params=None):
        self._conn.queries.append((query, params))
        try:
            return self._conn.results.get_nowait()
        except queue.Empty:
            return _Result()


class _Pg:
    """results: FIFO of _Result / row-list / single-row consumed per execute."""

    def __init__(self, results=()):
        self.results = queue.Queue()
        for item in results:
            if isinstance(item, _Result):
                self.results.put(item)
            else:
                self.results.put(_Result(item))
        self.queries = []
        self.commits = 0

    def cursor(self, **_kw):
        return _Cursor(self)

    def transaction(self):
        cm = unittest.mock.MagicMock()
        cm.__aenter__ = unittest.mock.AsyncMock(return_value=self)
        cm.__aexit__ = unittest.mock.AsyncMock(return_value=False)
        return cm

    async def commit(self):
        self.commits += 1

    async def close(self):
        pass


class _Publisher:
    def __init__(self, order=None):
        self.published = []
        self._order = order

    async def publish(self, message):
        self.published.append(message)
        if self._order is not None:
            self._order.append("publish")


class _Amqp:
    def __init__(self, order=None):
        self.publisher = _Publisher(order)
        self.calls = []

    async def get_publisher(self, exchange, routing_key):
        self.calls.append((exchange, routing_key))
        return self.publisher


def pg_results(*items):
    """Shorthand: each item is a row-list, a single row (fetchone target),
    or a pre-built _Result."""
    return _Pg(items)


def one(row):
    """Wrap a single row so fetchone returns it even inside a list arg."""
    return _Result(fetchone=row)
