"""profile service — the base profile with ids, for clients that write their
own tailored resume (the personal MCP server).

Run: .venv/bin/python -m pytest backend/api/tests/test_profile_service.py -v
"""

import unittest

from api.profile import service
from fastapi import HTTPException

from .helpers import _Pg, _Result, one

HEADER = ("Jane Doe", "jane@example.com", "+1 555 0100", "Brooklyn", None)


def _pg(header=HEADER, links=(), exps=(), skills=(), edu=(), projects=()):
    return _Pg(
        [
            one(header) if header else _Result(),
            _Result(list(links)),
            _Result(list(exps)),
            _Result(list(skills)),
            _Result(list(edu)),
            _Result(list(projects)),
        ]
    )


class GetProfile(unittest.IsolatedAsyncioTestCase):
    async def test_groups_bullets_under_their_experience_in_order(self):
        pg = _pg(
            exps=[
                (2, "Acme", "Senior Engineer", "2022", None, None, 20, "Led x"),
                (2, "Acme", "Senior Engineer", "2022", None, None, 21, "Built y"),
                (1, "Initech", "Engineer", "2019", "2022", "Payments", 10, "Ran z"),
            ]
        )
        profile = await service.get_profile(pg, "u1")
        self.assertEqual([e.id for e in profile.experiences], [2, 1])
        acme = profile.experiences[0]
        self.assertEqual(acme.company_name, "Acme")
        self.assertIsNone(acme.end_date)
        self.assertEqual(
            [(b.id, b.text) for b in acme.bullets], [(20, "Led x"), (21, "Built y")]
        )
        self.assertEqual(profile.experiences[1].description, "Payments")

    async def test_experience_without_bullets_keeps_an_empty_list(self):
        # LEFT JOIN: a bullet-less experience comes back with NULL bullet cols.
        pg = _pg(exps=[(3, "Hooli", "Intern", "2018", "2018", None, None, None)])
        profile = await service.get_profile(pg, "u1")
        self.assertEqual(profile.experiences[0].bullets, [])

    async def test_header_links_skills_education_projects(self):
        pg = _pg(
            links=[("LINKEDIN", "https://linkedin.com/in/jane")],
            skills=[("Python", "Languages"), ("Go", "Languages"), ("Kafka", None)],
            edu=[("MIT", "BS", "CS", "2014", "2018", None)],
            projects=[("Ledger", "https://x.dev", "A ledger", "2020", None)],
        )
        profile = await service.get_profile(pg, "u1")
        self.assertEqual(profile.full_name, "Jane Doe")
        self.assertEqual(profile.location, "Brooklyn")
        self.assertEqual(profile.social_links[0].type, "LINKEDIN")
        self.assertEqual(
            [(s.name, s.category) for s in profile.skills],
            [("Python", "Languages"), ("Go", "Languages"), ("Kafka", None)],
        )
        self.assertEqual(profile.education[0].field_of_study, "CS")
        self.assertEqual(profile.projects[0].link, "https://x.dev")

    async def test_every_query_is_scoped_to_the_user(self):
        pg = _pg()
        await service.get_profile(pg, "u1")
        self.assertEqual(len(pg.queries), 6)
        for _query, params in pg.queries:
            self.assertEqual(list(params), ["u1"])

    async def test_missing_user_row_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.get_profile(_pg(header=None), "u1")
        self.assertEqual(ctx.exception.status_code, 404)
