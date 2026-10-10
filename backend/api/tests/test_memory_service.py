"""memory service — list and save memory-bank facts over the API.

The SQL itself runs against a live Postgres in test_mcp_endpoints_pg.py; these
pin the request model and the save loop's decisions.

Run: .venv/bin/python -m pytest backend/api/tests/test_memory_service.py -v
"""

import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from api.memory import model, service
from fastapi import HTTPException
from pydantic import ValidationError
from shared.memory import MAX_FACT_CHARS, MAX_TOPIC_CHARS

from .helpers import _Pg, _Result, one

WHEN = datetime(2026, 10, 1, tzinfo=UTC)


def _req(*facts):
    return model.RememberRequest(facts=[model.NewMemoryFact(**f) for f in facts])


class RequestModel(unittest.TestCase):
    def test_strips_topic_and_content(self):
        fact = model.NewMemoryFact(topic="  General ", content=" Likes Go\n")
        self.assertEqual((fact.topic, fact.content), ("General", "Likes Go"))

    def test_blank_fields_rejected(self):
        with self.assertRaises(ValidationError):
            model.NewMemoryFact(topic="   ", content="x")
        with self.assertRaises(ValidationError):
            model.NewMemoryFact(topic="General", content="")

    def test_length_caps_match_the_bank(self):
        model.NewMemoryFact(topic="t" * MAX_TOPIC_CHARS, content="c" * MAX_FACT_CHARS)
        with self.assertRaises(ValidationError):
            model.NewMemoryFact(topic="t" * (MAX_TOPIC_CHARS + 1), content="c")
        with self.assertRaises(ValidationError):
            model.NewMemoryFact(topic="t", content="c" * (MAX_FACT_CHARS + 1))

    def test_empty_batch_rejected(self):
        with self.assertRaises(ValidationError):
            model.RememberRequest(facts=[])


class ListMemory(unittest.IsolatedAsyncioTestCase):
    async def test_rows_become_items(self):
        pg = _Pg([_Result([(4, "General", "Likes Go", "USER", WHEN)])])
        resp = await service.list_memory(pg, "u1")
        self.assertEqual(len(resp.facts), 1)
        fact = resp.facts[0]
        self.assertEqual((fact.id, fact.topic, fact.source), (4, "General", "USER"))
        self.assertEqual(fact.updated_at, WHEN.isoformat())
        self.assertEqual(list(pg.queries[0][1]), ["u1"])


class Remember(unittest.IsolatedAsyncioTestCase):
    async def test_new_fact_is_inserted_as_tailor_source(self):
        pg = _Pg(
            [
                one((1,)),  # share_user_row
                one((3,)),  # count
                _Result(),  # no identical fact
                one((9, "General", "Likes Go")),  # INSERT ... RETURNING
            ]
        )
        resp = await service.remember(
            pg, "u1", _req({"topic": "General", "content": "Likes Go"})
        )
        self.assertEqual([(f.id, f.content) for f in resp.saved], [(9, "Likes Go")])
        self.assertEqual(resp.full, 0)
        insert, params = pg.queries[-1]
        self.assertIn("INSERT INTO user_memory_fact", insert)
        self.assertIn("TAILOR", params)

    async def test_identical_fact_is_not_stored_twice(self):
        pg = _Pg([one((1,)), one((3,)), one((5, "General", "Likes Go"))])
        resp = await service.remember(
            pg, "u1", _req({"topic": "General", "content": "Likes Go"})
        )
        self.assertEqual([f.id for f in resp.saved], [5])
        self.assertFalse(any("INSERT" in q for q, _ in pg.queries))

    async def test_replaces_id_rewrites_in_place(self):
        pg = _Pg([one((1,)), one((3,)), one((5, "General", "Likes Go and Rust"))])
        resp = await service.remember(
            pg,
            "u1",
            _req(
                {"topic": "General", "content": "Likes Go and Rust", "replaces_id": 5}
            ),
        )
        self.assertEqual([f.id for f in resp.saved], [5])
        update, params = pg.queries[2]
        self.assertIn("UPDATE user_memory_fact", update)
        # Scoped to the caller, so another user's id can't be rewritten.
        self.assertIn("u1", params)

    async def test_unknown_replaces_id_falls_through_to_insert(self):
        pg = _Pg(
            [
                one((1,)),
                one((3,)),
                _Result(),  # UPDATE matched nothing (someone else's id)
                _Result(),  # no identical fact
                one((10, "General", "Likes Go")),
            ]
        )
        resp = await service.remember(
            pg,
            "u1",
            _req({"topic": "General", "content": "Likes Go", "replaces_id": 77}),
        )
        self.assertEqual([f.id for f in resp.saved], [10])

    async def test_full_bank_counts_turned_away_facts(self):
        with patch.object(service, "MAX_MEMORY_FACTS", 1):
            pg = _Pg([one((1,)), one((1,)), _Result()])
            resp = await service.remember(
                pg, "u1", _req({"topic": "General", "content": "Likes Go"})
            )
        self.assertEqual(resp.saved, [])
        self.assertEqual(resp.full, 1)

    async def test_deleted_account_404(self):
        pg = _Pg([_Result()])  # share_user_row finds no user row
        with self.assertRaises(HTTPException) as ctx:
            await service.remember(pg, "u1", _req({"topic": "General", "content": "x"}))
        self.assertEqual(ctx.exception.status_code, 404)
