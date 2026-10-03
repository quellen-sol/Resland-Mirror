"""Curated system design bank — file integrity (every reference design is a
connected graph over known component kinds), brief round-tripping, and the
random picker.

Run: .venv/bin/python -m unittest backend.shared.tests.test_system_design_bank -v
"""

import random
import unittest

from shared.system_design import bank
from shared.system_design.diagram import COMPONENT_KINDS


class BankIntegrity(unittest.TestCase):
    def setUp(self):
        self.problems = bank.list_problems()

    def test_bank_is_not_empty_and_ids_are_unique(self):
        self.assertGreaterEqual(len(self.problems), 10)
        ids = [p.id for p in self.problems]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_problem_is_complete(self):
        for p in self.problems:
            with self.subTest(problem=p.id):
                self.assertIn(p.difficulty, bank.DIFFICULTIES)
                self.assertTrue(p.title and p.summary and p.brief.prompt)
                self.assertEqual(p.brief.title, p.title)
                self.assertTrue(p.tags)
                for attr in (
                    "clarifications",
                    "functional_requirements",
                    "non_functional_requirements",
                    "estimation_notes",
                    "reference_components",
                    "reference_connections",
                    "deep_dive_topics",
                    "pitfalls",
                ):
                    self.assertTrue(getattr(p.brief, attr), attr)

    def test_reference_designs_are_connected_graphs_of_known_kinds(self):
        for p in self.problems:
            with self.subTest(problem=p.id):
                ids = {c.id for c in p.brief.reference_components}
                self.assertEqual(len(ids), len(p.brief.reference_components))
                for c in p.brief.reference_components:
                    self.assertIn(c.kind, COMPONENT_KINDS)
                used = set()
                for conn in p.brief.reference_connections:
                    self.assertIn(conn.source, ids)
                    self.assertIn(conn.target, ids)
                    used |= {conn.source, conn.target}
                self.assertEqual(used, ids)

    def test_entries_are_typed(self):
        p = self.problems[0]
        self.assertIsInstance(p.brief.clarifications[0], bank.Clarification)
        self.assertIsInstance(p.brief.reference_components[0], bank.RefComponent)
        self.assertIsInstance(p.brief.reference_connections[0], bank.RefConnection)
        self.assertIsInstance(p.tags, tuple)


class Lookup(unittest.TestCase):
    def test_get_problem(self):
        first = bank.list_problems()[0]
        self.assertIs(bank.get_problem(first.id), first)
        self.assertIsNone(bank.get_problem("nope"))


class BriefSerialization(unittest.TestCase):
    def test_round_trip(self):
        brief = bank.list_problems()[0].brief
        self.assertEqual(bank.InterviewBrief.from_json(brief.to_json()), brief)

    def test_from_dict_tolerates_missing_lists_and_extra_keys(self):
        brief = bank.InterviewBrief.from_dict(
            {
                "title": "T",
                "prompt": "P",
                "clarifications": [{"topic": "Scale", "answer": "Big"}],
                "reference_components": [
                    {
                        "id": "a",
                        "kind": "service",
                        "label": "A",
                        "purpose": "x",
                        "extra": 1,
                    }
                ],
                "reference_connections": [{"source": "a", "target": "a"}],
                "something_new": True,
            }
        )
        self.assertEqual(brief.clarifications, (bank.Clarification("Scale", "Big"),))
        self.assertEqual(brief.reference_connections[0].label, "")
        self.assertEqual(brief.pitfalls, ())


class PickRandom(unittest.TestCase):
    def test_avoids_excluded_problems(self):
        ids = [p.id for p in bank.list_problems()]
        keep = ids[-1]
        for seed in range(20):
            picked = bank.pick_random(set(ids) - {keep}, random.Random(seed))
            self.assertEqual(picked.id, keep)

    def test_falls_back_when_everything_was_seen(self):
        ids = {p.id for p in bank.list_problems()}
        self.assertIn(bank.pick_random(ids, random.Random(1)).id, ids)

    def test_seeded_rng_is_deterministic(self):
        a = bank.pick_random(rng=random.Random(7))
        b = bank.pick_random(rng=random.Random(7))
        self.assertEqual(a.id, b.id)


if __name__ == "__main__":
    unittest.main()
