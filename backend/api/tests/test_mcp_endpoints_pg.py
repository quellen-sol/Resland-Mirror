"""The endpoints the personal MCP server calls (GET /profile, GET/POST
/memory, POST /tailored), against a live Postgres (TEST_PG_URL).

Run: .venv/bin/python -m pytest backend/api/tests/test_mcp_endpoints_pg.py -v
"""

from unittest.mock import patch

import pytest
from api.memory import model as memory_model
from api.memory import service as memory_service
from api.profile import service as profile_service
from api.tailored import model as tailored_model
from api.tailored import service as tailored_service
from fastapi import HTTPException

OTHER = "u2"


async def _experience(pg, user_id, company, title, start, end, bullets, created_at):
    res = await pg.execute(
        """
        INSERT INTO user_base_experience
            (user_id, company_name, title, start_date, end_date, created_at)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """,
        (user_id, company, title, start, end, created_at),
    )
    exp_id = (await res.fetchone())[0]
    bullet_ids = []
    for order, text in enumerate(bullets):
        res = await pg.execute(
            """
            INSERT INTO user_base_experience_bullet
                (user_experience_id, bullet, bullet_order)
            VALUES (%s, %s, %s) RETURNING id
            """,
            (exp_id, text, order),
        )
        bullet_ids.append((await res.fetchone())[0])
    return exp_id, bullet_ids


@pytest.fixture
async def profile(pg, user):
    await pg.execute(
        """
        UPDATE "user" SET full_name = 'Jane Doe', email = 'jane@example.com',
            location = 'Brooklyn' WHERE auth0_id = %s
        """,
        (user,),
    )
    await pg.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', (OTHER,))
    await pg.execute(
        "INSERT INTO user_social_link (user_id, type, link) VALUES (%s, 'GITHUB', %s)",
        (user, "https://github.com/jane"),
    )
    # Inserted in the opposite of display order: newest created_at first.
    old_id, _ = await _experience(
        pg, user, "Initech", "Engineer", "2019", "2022", ["Ran z"], "2024-01-01"
    )
    new_id, new_bullets = await _experience(
        pg,
        user,
        "Acme",
        "Senior Engineer",
        "2022",
        None,
        ["Led x", "Built y"],
        "2025-01-01",
    )
    bare_id, _ = await _experience(
        pg, user, "Hooli", "Intern", "2018", "2018", [], "2023-01-01"
    )
    await _experience(
        pg, OTHER, "Elsewhere", "CTO", "2010", None, ["Secret"], "2025-06-01"
    )
    for order, (name, category) in enumerate(
        [("Python", "Languages"), ("Go", "Languages"), ("Kafka", "Data")]
    ):
        await pg.execute(
            """
            INSERT INTO user_base_skill (user_id, name, category, sort_order)
            VALUES (%s, %s, %s, %s)
            """,
            (user, name, category, order),
        )
    await pg.execute(
        """
        INSERT INTO user_base_education
            (user_id, institution, degree, field_of_study, start_date, end_date)
        VALUES (%s, 'MIT', 'BS', 'CS', '2014', '2018')
        """,
        (user,),
    )
    await pg.execute(
        """
        INSERT INTO user_base_project (user_id, name, link, start_date)
        VALUES (%s, 'Ledger', 'https://x.dev', '2020')
        """,
        (user,),
    )
    return {"new": new_id, "old": old_id, "bare": bare_id, "new_bullets": new_bullets}


# Profile ----------------------------------------------------------------


async def test_profile_reads_the_users_rows_in_display_order(pg, profile):
    resp = await profile_service.get_profile(pg, "u1")
    assert resp.full_name == "Jane Doe"
    assert [(s.type, s.link) for s in resp.social_links] == [
        ("GITHUB", "https://github.com/jane")
    ]
    # Newest created_at first: Acme (2025), Initech (2024), Hooli (2023).
    assert [e.id for e in resp.experiences] == [
        profile["new"],
        profile["old"],
        profile["bare"],
    ]
    acme = resp.experiences[0]
    assert [b.id for b in acme.bullets] == profile["new_bullets"]
    assert [b.text for b in acme.bullets] == ["Led x", "Built y"]
    assert resp.experiences[2].bullets == []
    assert [s.name for s in resp.skills] == ["Python", "Go", "Kafka"]
    assert resp.education[0].institution == "MIT"
    assert resp.projects[0].name == "Ledger"
    assert "Elsewhere" not in resp.model_dump_json()


async def test_profile_of_a_missing_user_404(pg):
    with pytest.raises(HTTPException) as exc:
        await profile_service.get_profile(pg, "nobody")
    assert exc.value.status_code == 404


# Memory -----------------------------------------------------------------


def _remember(*facts):
    return memory_model.RememberRequest(
        facts=[memory_model.NewMemoryFact(**f) for f in facts]
    )


async def test_remember_stores_dedupes_and_rewrites(pg, user):
    first = await memory_service.remember(
        pg,
        user,
        _remember(
            {
                "topic": "Senior Engineer at Acme",
                "content": "Ledger handled 2M payments a day",
            },
            {"topic": "Preferences", "content": "No summary"},
        ),
    )
    assert first.full == 0
    ledger_id, prefs_id = (f.id for f in first.saved)

    # The same fact again is not stored twice.
    again = await memory_service.remember(
        pg, user, _remember({"topic": "Preferences", "content": "No summary"})
    )
    assert [f.id for f in again.saved] == [prefs_id]

    # replaces_id rewrites in place.
    rewritten = await memory_service.remember(
        pg,
        user,
        _remember(
            {
                "topic": "Senior Engineer at Acme",
                "content": "Ledger handled 3M payments a day",
                "replaces_id": ledger_id,
            }
        ),
    )
    assert [f.id for f in rewritten.saved] == [ledger_id]

    listed = await memory_service.list_memory(pg, user)
    assert [(f.id, f.topic, f.content, f.source) for f in listed.facts] == [
        (prefs_id, "Preferences", "No summary", "TAILOR"),
        (
            ledger_id,
            "Senior Engineer at Acme",
            "Ledger handled 3M payments a day",
            "TAILOR",
        ),
    ]


async def test_remember_cannot_rewrite_another_users_fact(pg, user):
    await pg.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', (OTHER,))
    res = await pg.execute(
        """
        INSERT INTO user_memory_fact (user_id, topic, content, source)
        VALUES (%s, 'General', 'Theirs', 'USER') RETURNING id
        """,
        (OTHER,),
    )
    theirs = (await res.fetchone())[0]
    resp = await memory_service.remember(
        pg,
        user,
        _remember({"topic": "General", "content": "Mine", "replaces_id": theirs}),
    )
    assert resp.saved[0].id != theirs
    res = await pg.execute(
        "SELECT content FROM user_memory_fact WHERE id = %s", (theirs,)
    )
    assert (await res.fetchone())[0] == "Theirs"
    assert (await memory_service.list_memory(pg, OTHER)).facts[0].content == "Theirs"


async def test_remember_stops_at_the_bank_cap(pg, user):
    with patch.object(memory_service, "MAX_MEMORY_FACTS", 1):
        resp = await memory_service.remember(
            pg,
            user,
            _remember(
                {"topic": "General", "content": "One"},
                {"topic": "General", "content": "Two"},
            ),
        )
    assert [f.content for f in resp.saved] == ["One"]
    assert resp.full == 1


async def test_remember_for_a_deleted_account_404(pg):
    with pytest.raises(HTTPException) as exc:
        await memory_service.remember(
            pg, "nobody", _remember({"topic": "General", "content": "x"})
        )
    assert exc.value.status_code == 404


# Tailored ---------------------------------------------------------------


async def test_create_tailored_round_trips_through_get(pg, profile):
    req = tailored_model.CreateTailoredRequest(
        company_name="Globex",
        role="Staff Engineer",
        job_description="Build payment rails",
        experiences=[
            {"experience_id": profile["new"], "bullets": ["Built the rails"]},
            {"experience_id": profile["bare"], "bullets": []},
            {"experience_id": profile["old"], "bullets": ["Ran z"]},
        ],
        skills=["Kafka", "Go", "Python"],
    )
    created = await tailored_service.create_tailored(pg, "u1", req)
    got = await tailored_service.get_tailored(pg, "u1", created.id)
    assert (got.company_name, got.role, got.job_description) == (
        "Globex",
        "Staff Engineer",
        "Build payment rails",
    )
    assert [(e.company_name, e.bullets) for e in got.content.experiences] == [
        ("Acme", ["Built the rails"]),
        ("Hooli", []),
        ("Initech", ["Ran z"]),
    ]
    assert [(g.category, g.skills) for g in got.content.skill_groups] == [
        ("Data", ["Kafka"]),
        ("Languages", ["Go", "Python"]),
    ]
    # Two saves of hand-written content are two board entries, not one.
    second = await tailored_service.create_tailored(pg, "u1", req)
    assert second.id != created.id


async def test_create_tailored_rejects_another_users_experience(pg, profile):
    res = await pg.execute(
        "SELECT id FROM user_base_experience WHERE user_id = %s", (OTHER,)
    )
    theirs = (await res.fetchone())[0]
    req = tailored_model.CreateTailoredRequest(
        job_description="JD", experiences=[{"experience_id": theirs, "bullets": ["x"]}]
    )
    with pytest.raises(HTTPException) as exc:
        await tailored_service.create_tailored(pg, "u1", req)
    assert exc.value.status_code == 422
