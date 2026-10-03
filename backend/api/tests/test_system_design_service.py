"""System design service tests — need a live Postgres (TEST_PG_URL).

The service runs against real SQL through system_design/db.py; AMQP is the
helpers' fake publisher, so each test can read back exactly what was queued.
"""

import json

try:
    import pytest
except ImportError:
    # unittest discovery has no pytest — this module is all pytest-function
    # tests, so it collects zero tests under unittest; the stub just keeps
    # the module importable.
    class _PytestStub:
        @staticmethod
        def fixture(*_a, **_kw):
            return lambda g: g

        def __getattr__(self, name):
            raise ImportError("pytest is required to run this test")

    pytest = _PytestStub()
from api.system_design import model, service
from fastapi import HTTPException
from shared.amqp import SYSTEM_DESIGN_EXCHANGE_NAME
from shared.system_design import bank

from .helpers import _Amqp

PROBLEM = bank.list_problems()[0]

SCENE = [
    {"id": "c", "type": "rectangle", "isDeleted": False},
    {"id": "c-t", "type": "text", "text": "Client", "containerId": "c"},
    {"id": "s", "type": "rectangle", "isDeleted": False},
    {"id": "s-t", "type": "text", "text": "API", "containerId": "s"},
    {
        "id": "e",
        "type": "arrow",
        "startBinding": {"elementId": "c"},
        "endBinding": {"elementId": "s"},
        "endArrowhead": "arrow",
    },
]


@pytest.fixture
async def funded(pg, user):
    await pg.execute(
        'UPDATE "user" SET balance_cents = 500 WHERE auth0_id = %s', (user,)
    )
    return user


async def _seed(pg, sid="s1", user_id="u1", **cols):
    base = {
        "source": "BANK",
        "problem_id": PROBLEM.id,
        "status": "WAITING_FOR_INPUT",
        "phase": "REQUIREMENTS",
        "title": PROBLEM.title,
        "prompt": PROBLEM.brief.prompt,
        "brief": PROBLEM.brief.to_json(),
    }
    base.update(cols)
    names = ", ".join(["id", "user_id", *base])
    marks = ", ".join(["%s"] * (len(base) + 2))
    await pg.execute(
        f"INSERT INTO user_system_design_session ({names}) VALUES ({marks})",
        (sid, user_id, *base.values()),
    )
    return sid


async def _row(pg, sid="s1"):
    cur = await pg.execute(
        "SELECT * FROM user_system_design_session WHERE id = %s", (sid,)
    )
    cols = [c.name for c in cur.description]
    row = await cur.fetchone()
    return dict(zip(cols, row)) if row else None


async def _messages(pg, sid="s1"):
    cur = await pg.execute(
        "SELECT role, phase, content FROM system_design_message"
        " WHERE session_id = %s ORDER BY id",
        (sid,),
    )
    return await cur.fetchall()


def _published(amqp):
    return [json.loads(m.body) for m in amqp.publisher.published]


async def _turn(pg, amqp=None, sid="s1", **req):
    return await service.take_turn(
        pg, amqp or _Amqp(), "u1", sid, model.TurnRequest(**req)
    )


async def _expect(status, coro):
    with pytest.raises(HTTPException) as exc:
        await coro
    assert exc.value.status_code == status
    return exc.value


# Problems ---------------------------------------------------------------


def test_list_problems_comes_from_the_bank():
    resp = service.list_problems()
    assert [p.id for p in resp.problems] == [p.id for p in bank.list_problems()]
    first = resp.problems[0]
    assert first.title == PROBLEM.title
    assert first.tags == list(PROBLEM.tags)
    # The picker never sees the interviewer's brief.
    assert "brief" not in first.model_dump()


# Start ----------------------------------------------------------------


async def test_start_bank_session_publishes_start_job(pg, funded):
    amqp = _Amqp()
    resp = await service.start_system_design(
        pg,
        amqp,
        model.StartSystemDesignRequest(
            source="BANK", problem_id=PROBLEM.id, level="STAFF"
        ),
        funded,
    )
    assert not resp.resumed
    row = await _row(pg, resp.session_id)
    assert row["source"] == "BANK"
    assert row["problem_id"] == PROBLEM.id
    assert row["level"] == "STAFF"
    assert row["status"] == "PROCESSING"
    assert amqp.calls == [(SYSTEM_DESIGN_EXCHANGE_NAME, "#")]
    job = _published(amqp)[0]
    assert job["session_id"] == resp.session_id
    assert job["action"] == "start"
    assert job["turn_id"]


async def test_start_random_avoids_practiced_problems(pg, funded):
    ids = [p.id for p in bank.list_problems()]
    for i, pid in enumerate(ids[:-1]):
        await _seed(pg, f"done-{i}", problem_id=pid, status="COMPLETED")
    resp = await service.start_system_design(
        pg, _Amqp(), model.StartSystemDesignRequest(source="BANK"), funded
    )
    assert (await _row(pg, resp.session_id))["problem_id"] == ids[-1]


async def test_start_unknown_problem_404(pg, funded):
    await _expect(
        404,
        service.start_system_design(
            pg,
            _Amqp(),
            model.StartSystemDesignRequest(source="BANK", problem_id="nope"),
            funded,
        ),
    )


async def test_start_needs_balance(pg, user):
    await _expect(
        402,
        service.start_system_design(
            pg, _Amqp(), model.StartSystemDesignRequest(source="BANK"), user
        ),
    )


async def test_start_resumes_an_unfinished_session(pg, funded):
    await _seed(pg, "open", status="FAILED")
    amqp = _Amqp()
    resp = await service.start_system_design(
        pg, amqp, model.StartSystemDesignRequest(source="BANK"), funded
    )
    assert resp.session_id == "open"
    assert resp.resumed
    assert amqp.publisher.published == []


async def test_start_job_snapshots_the_tailored_posting(pg, funded):
    await pg.execute(
        "INSERT INTO user_tailored_resume (id, user_id, company_name, role,"
        " job_description, content) VALUES ('t1', %s, 'Stripe', 'Backend', 'Payouts in Go', '{}')",
        (funded,),
    )
    resp = await service.start_system_design(
        pg,
        _Amqp(),
        model.StartSystemDesignRequest(source="JOB", tailored_resume_id="t1"),
        funded,
    )
    row = await _row(pg, resp.session_id)
    assert row["source"] == "JOB"
    assert row["problem_id"] is None
    assert row["tailored_resume_id"] == "t1"
    assert (row["company_name"], row["role"], row["job_description"]) == (
        "Stripe",
        "Backend",
        "Payouts in Go",
    )


async def test_start_job_needs_a_resume_of_your_own(pg, funded):
    await _expect(
        400,
        service.start_system_design(
            pg, _Amqp(), model.StartSystemDesignRequest(source="JOB"), funded
        ),
    )
    await pg.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', ("u2",))
    await pg.execute(
        "INSERT INTO user_tailored_resume (id, user_id, job_description, content)"
        " VALUES ('theirs', 'u2', 'JD', '{}')"
    )
    await _expect(
        404,
        service.start_system_design(
            pg,
            _Amqp(),
            model.StartSystemDesignRequest(source="JOB", tailored_resume_id="theirs"),
            funded,
        ),
    )


async def test_unknown_model_400(pg, funded):
    await _expect(
        400,
        service.start_system_design(
            pg,
            _Amqp(),
            model.StartSystemDesignRequest(source="BANK", model="evil/model"),
            funded,
        ),
    )


# Status -----------------------------------------------------------------


async def test_status_hides_the_brief_until_completed(pg, user):
    await _seed(pg, phase_durations='{"REQUIREMENTS": 120}')
    await pg.execute(
        "INSERT INTO system_design_message (session_id, role, phase, content)"
        " VALUES ('s1', 'INTERVIEWER', 'REQUIREMENTS', 'Hi')"
    )
    resp = await service.get_status(pg, user, "s1")
    assert resp.status == "WAITING_FOR_INPUT"
    assert resp.title == PROBLEM.title
    assert resp.result is None and resp.reference is None
    assert resp.phase_durations == {"REQUIREMENTS": 120}
    assert resp.phase_targets["HIGH_LEVEL_DESIGN"] == 15 * 60
    assert [(m.role, m.content) for m in resp.messages] == [("INTERVIEWER", "Hi")]
    assert resp.server_time.tzinfo is not None


async def test_status_reveals_report_and_reference_when_completed(pg, user):
    await _seed(
        pg,
        status="COMPLETED",
        phase="FEEDBACK",
        result=json.dumps({"letter_grade": "B+"}),
        letter_grade="B+",
        hire_signal="HIRE",
    )
    resp = await service.get_status(pg, user, "s1")
    assert resp.result == {"letter_grade": "B+"}
    assert resp.letter_grade == "B+"
    assert resp.reference["reference_components"]
    assert resp.reference["title"] == PROBLEM.title


async def test_other_users_session_404(pg, user):
    await pg.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', ("u2",))
    await _seed(pg, "theirs", user_id="u2")
    await _expect(404, service.get_status(pg, user, "theirs"))
    await _expect(404, service.get_workspace(pg, user, "theirs"))
    await _expect(404, _turn(pg, sid="theirs", action="message", text="hi"))


async def test_active(pg, user):
    await _expect(404, service.get_active(pg, user))
    await _seed(pg, "old", status="COMPLETED")
    await _seed(pg, "live")
    assert (await service.get_active(pg, user)).session_id == "live"


# Workspace ---------------------------------------------------------------


async def test_workspace_round_trip_reports_issues(pg, user):
    await _seed(pg)
    scene = [*SCENE, {"id": "x", "type": "rectangle", "isDeleted": False}]
    saved = await service.save_workspace(
        pg, user, "s1", model.Workspace(diagram=json.dumps(scene), requirements="R1")
    )
    assert [i.kind for i in saved.issues] == ["orphan_node"]
    again = await service.get_workspace(pg, user, "s1")
    assert again.requirements == "R1"
    assert again.estimates == ""
    assert json.loads(again.diagram) == scene
    # Omitted fields are left alone.
    await service.save_workspace(pg, user, "s1", model.Workspace(estimates="E1"))
    row = await _row(pg)
    assert (row["requirements"], row["estimates"]) == ("R1", "E1")


async def test_workspace_locked_once_finished(pg, user):
    await _seed(pg, status="COMPLETED")
    await _expect(
        409, service.save_workspace(pg, user, "s1", model.Workspace(requirements="x"))
    )


# Turns -----------------------------------------------------------------


async def test_turn_waits_for_the_interviewer(pg, funded):
    await _seed(pg, status="PROCESSING")
    await _expect(409, _turn(pg, action="message", text="hi"))


async def test_message_turn_records_and_publishes(pg, funded):
    await _seed(pg)
    amqp = _Amqp()
    resp = await _turn(
        pg,
        amqp,
        action="message",
        text="  How many users?  ",
        workspace={"requirements": "Shorten links"},
    )
    assert resp.phase == "REQUIREMENTS"
    row = await _row(pg)
    assert row["status"] == "PROCESSING"
    assert row["requirements"] == "Shorten links"
    assert await _messages(pg) == [("CANDIDATE", "REQUIREMENTS", "How many users?")]
    job = _published(amqp)[0]
    assert (job["action"], job["text"]) == ("message", "How many users?")


async def test_message_turn_needs_text(pg, funded):
    await _seed(pg)
    await _expect(400, _turn(pg, action="message", text="   "))


async def test_turn_needs_balance(pg, user):
    await _seed(pg)
    await _expect(402, _turn(pg, action="message", text="hi"))
    assert (await _row(pg))["status"] == "WAITING_FOR_INPUT"
    assert await _messages(pg) == []


async def test_advance_moves_phase_and_records_time(pg, funded):
    await _seed(pg)
    await pg.execute(
        "UPDATE user_system_design_session SET phase_started_at = now() - interval '7 minutes'"
    )
    amqp = _Amqp()
    resp = await _turn(pg, amqp, action="advance")
    assert resp.phase == "ESTIMATION"
    row = await _row(pg)
    assert row["phase"] == "ESTIMATION"
    assert abs(json.loads(row["phase_durations"])["REQUIREMENTS"] - 420) <= 5
    assert await _messages(pg) == []
    assert _published(amqp)[0]["action"] == "advance"


async def test_advance_from_design_rejects_an_empty_diagram(pg, funded):
    await _seed(pg, phase="HIGH_LEVEL_DESIGN")
    err = await _expect(422, _turn(pg, action="advance"))
    assert err.detail["code"] == "empty_diagram"


async def test_advance_from_design_reports_issues_until_acknowledged(pg, funded):
    await _seed(pg, phase="HIGH_LEVEL_DESIGN")
    half = {**SCENE[-1], "id": "half", "endBinding": None}
    workspace = {"diagram": json.dumps([*SCENE, half])}
    err = await _expect(422, _turn(pg, action="advance", workspace=workspace))
    assert err.detail["code"] == "diagram_issues"
    assert err.detail["issues"][0]["element_id"] == "half"
    # The diagram was saved even though the turn was refused.
    assert "half" in (await _row(pg))["diagram"]
    assert (await _row(pg))["status"] == "WAITING_FOR_INPUT"

    resp = await _turn(pg, action="advance", acknowledge_issues=True)
    assert resp.phase == "DEEP_DIVE"


async def test_advance_from_a_clean_design(pg, funded):
    await _seed(pg, phase="HIGH_LEVEL_DESIGN", diagram=json.dumps(SCENE))
    assert (
        await _turn(pg, action="advance", text="Here's my design")
    ).phase == "DEEP_DIVE"
    assert await _messages(pg) == [
        ("CANDIDATE", "HIGH_LEVEL_DESIGN", "Here's my design")
    ]


async def test_no_advancing_out_of_the_deep_dive(pg, funded):
    await _seed(pg, phase="DEEP_DIVE")
    await _expect(409, _turn(pg, action="advance"))


async def test_finish_moves_to_feedback(pg, funded):
    await _seed(pg, phase="ESTIMATION")
    amqp = _Amqp()
    assert (await _turn(pg, amqp, action="finish")).phase == "FEEDBACK"
    row = await _row(pg)
    assert row["phase"] == "FEEDBACK"
    assert "ESTIMATION" in json.loads(row["phase_durations"])
    assert _published(amqp)[0]["action"] == "finish"


async def test_finish_needs_a_started_interview(pg, funded):
    await _seed(pg, title=None, brief=None, notice="Something broke")
    await _expect(409, _turn(pg, action="finish"))


async def test_notice_only_allows_retry_or_finish(pg, funded):
    await _seed(pg, notice="Something broke")
    await _expect(409, _turn(pg, action="message", text="hi"))
    amqp = _Amqp()
    await _turn(pg, amqp, action="retry")
    row = await _row(pg)
    assert row["notice"] is None
    assert row["status"] == "PROCESSING"
    assert _published(amqp)[0]["action"] == "retry"


async def test_retry_needs_something_to_retry(pg, funded):
    await _seed(pg)
    await _expect(409, _turn(pg, action="retry"))


async def test_feedback_phase_takes_no_messages(pg, funded):
    await _seed(pg, phase="FEEDBACK")
    await _expect(409, _turn(pg, action="message", text="hi"))
    await _expect(409, _turn(pg, action="finish"))


# Dismiss -----------------------------------------------------------------


async def test_dismiss_deletes_session_and_transcript(pg, user):
    await _seed(pg)
    await pg.execute(
        "INSERT INTO system_design_message (session_id, role, phase, content)"
        " VALUES ('s1', 'INTERVIEWER', 'REQUIREMENTS', 'Hi')"
    )
    assert await service.dismiss(pg, user, "s1") == {"ok": True}
    assert await _row(pg) is None
    assert await _messages(pg) == []


async def test_dismiss_leaves_other_users_alone(pg, user):
    await pg.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', ("u2",))
    await _seed(pg, "theirs", user_id="u2")
    await service.dismiss(pg, user, "theirs")
    assert await _row(pg, "theirs") is not None
