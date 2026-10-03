import json
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from shared.amqp import SYSTEM_DESIGN_EXCHANGE_NAME, AmqpSystemDesignJob
from shared.system_design import bank, rubric
from shared.system_design.diagram import normalize_scene, parse_scene

from ..balance import require_balance, validate_model_choice
from ..deps import AmqpClientDep, PgConnection
from . import db, model

# Sessions the candidate can still write to.
_OPEN_STATUSES = ("PROCESSING", "WAITING_FOR_INPUT")


def list_problems() -> model.ProblemsResponse:
    return model.ProblemsResponse(
        problems=[
            model.ProblemSummary(
                id=p.id,
                title=p.title,
                difficulty=p.difficulty,
                tags=list(p.tags),
                summary=p.summary,
            )
            for p in bank.list_problems()
        ]
    )


async def _publish(
    amqp_client: AmqpClientDep, session_id: str, action: str, text: str | None = None
) -> None:
    job = AmqpSystemDesignJob(session_id=session_id, action=action, text=text)
    publisher = await amqp_client.get_publisher(SYSTEM_DESIGN_EXCHANGE_NAME, "#")
    await publisher.publish(job.to_message())


async def start_system_design(
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
    req: model.StartSystemDesignRequest,
    user_id: str,
) -> model.StartSystemDesignResponse:
    active = await db.get_outstanding_session(pg_conn, user_id)
    if active:
        # One interview at a time — hand the unfinished one back to resume.
        return model.StartSystemDesignResponse(session_id=active.id, resumed=True)

    await require_balance(pg_conn, user_id)
    chosen_model = await validate_model_choice(pg_conn, req.model)

    problem_id = None
    posting = None
    if req.source == "BANK":
        if req.problem_id:
            problem = bank.get_problem(req.problem_id)
            if not problem:
                raise HTTPException(status_code=404, detail="Unknown problem")
        else:
            practiced = await db.practiced_problem_ids(pg_conn, user_id)
            problem = bank.pick_random(practiced)
        problem_id = problem.id
    else:
        if not req.tailored_resume_id:
            raise HTTPException(
                status_code=400, detail="Pick a tailored resume to practice for"
            )
        posting = await db.get_tailored_posting(
            pg_conn, user_id, req.tailored_resume_id
        )
        if not posting:
            raise HTTPException(status_code=404, detail="Tailored resume not found")
        if not posting.job_description.strip():
            raise HTTPException(
                status_code=400, detail="That tailored resume has no job posting"
            )

    session_id = str(uuid.uuid4())
    await db.create_session(
        pg_conn,
        session_id=session_id,
        user_id=user_id,
        source=req.source,
        problem_id=problem_id,
        tailored_resume_id=req.tailored_resume_id if posting else None,
        company_name=posting.company_name if posting else None,
        role=posting.role if posting else None,
        job_description=posting.job_description if posting else None,
        level=req.level,
        model=chosen_model,
    )
    # Commit before publishing so the dispatcher sees the row.
    await pg_conn.commit()
    await _publish(amqp_client, session_id, "start")
    return model.StartSystemDesignResponse(session_id=session_id)


async def _require_session(
    pg_conn: PgConnection, user_id: str, session_id: str
) -> db.SessionRow:
    row = await db.get_session(pg_conn, user_id, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Interview not found")
    return row


def _json_or(raw: str | None, default):
    try:
        return json.loads(raw) if raw else default
    except ValueError:
        return default


async def _to_status(
    pg_conn: PgConnection, row: db.SessionRow
) -> model.SessionStatusResponse:
    messages = await db.list_messages(pg_conn, row.id)
    completed = row.status == "COMPLETED"
    reference = None
    if completed and row.brief:
        reference = bank.InterviewBrief.from_json(row.brief).to_dict()
    return model.SessionStatusResponse(
        session_id=row.id,
        status=row.status,
        phase=row.phase,
        source=row.source,
        level=row.level,
        problem_id=row.problem_id,
        company_name=row.company_name,
        role=row.role,
        title=row.title,
        prompt=row.prompt,
        notice=row.notice,
        phase_started_at=row.phase_started_at,
        created_at=row.created_at,
        completed_at=row.completed_at,
        server_time=datetime.now(UTC),
        phase_durations=_json_or(row.phase_durations, {}),
        phase_targets=dict(rubric.PHASE_TARGET_SECONDS),
        messages=[
            model.Message(
                id=m.id,
                role=m.role,
                phase=m.phase,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
        letter_grade=row.letter_grade,
        hire_signal=row.hire_signal,
        result=_json_or(row.result, None) if completed else None,
        reference=reference,
    )


async def get_status(
    pg_conn: PgConnection, user_id: str, session_id: str
) -> model.SessionStatusResponse:
    return await _to_status(
        pg_conn, await _require_session(pg_conn, user_id, session_id)
    )


async def get_active(
    pg_conn: PgConnection, user_id: str
) -> model.SessionStatusResponse:
    row = await db.get_outstanding_session(pg_conn, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="No interview in progress")
    return await _to_status(pg_conn, row)


def _issues(diagram: str) -> list[model.DiagramIssue]:
    return [
        model.DiagramIssue(kind=i.kind, element_id=i.element_id, message=i.message)
        for i in normalize_scene(parse_scene(diagram)).issues()
    ]


def _to_workspace(row: db.SessionRow) -> model.WorkspaceResponse:
    return model.WorkspaceResponse(
        diagram=row.diagram,
        requirements=row.requirements,
        estimates=row.estimates,
        issues=_issues(row.diagram),
    )


async def get_workspace(
    pg_conn: PgConnection, user_id: str, session_id: str
) -> model.WorkspaceResponse:
    return _to_workspace(await _require_session(pg_conn, user_id, session_id))


async def save_workspace(
    pg_conn: PgConnection, user_id: str, session_id: str, req: model.Workspace
) -> model.WorkspaceResponse:
    row = await _require_session(pg_conn, user_id, session_id)
    if row.status not in _OPEN_STATUSES:
        raise HTTPException(status_code=409, detail="This interview is over")
    await db.save_workspace(
        pg_conn,
        session_id,
        diagram=req.diagram,
        requirements=req.requirements,
        estimates=req.estimates,
    )
    row = await _require_session(pg_conn, user_id, session_id)
    return _to_workspace(row)


async def take_turn(
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
    user_id: str,
    session_id: str,
    req: model.TurnRequest,
) -> model.TurnResponse:
    row = await _require_session(pg_conn, user_id, session_id)
    if row.status != "WAITING_FOR_INPUT":
        raise HTTPException(
            status_code=409, detail="The interviewer isn't waiting on you"
        )
    action = req.action
    if row.notice and action not in ("retry", "finish"):
        raise HTTPException(status_code=409, detail="Retry the last turn first")
    if action == "retry" and not row.notice:
        raise HTTPException(status_code=409, detail="Nothing to retry")
    if action == "finish" and not row.brief:
        raise HTTPException(status_code=409, detail="The interview hasn't started")
    if row.phase == "FEEDBACK" and action != "retry":
        raise HTTPException(status_code=409, detail="The interview is over")
    if action == "advance" and row.phase not in rubric.ADVANCEABLE_PHASES:
        raise HTTPException(
            status_code=409, detail="The deep dive ends when the interview does"
        )
    text = (req.text or "").strip()
    if action == "message" and not text:
        raise HTTPException(status_code=400, detail="Say something first")

    await require_balance(pg_conn, user_id)

    if req.workspace:
        await db.save_workspace(
            pg_conn,
            session_id,
            diagram=req.workspace.diagram,
            requirements=req.workspace.requirements,
            estimates=req.workspace.estimates,
        )
        row = await _require_session(pg_conn, user_id, session_id)

    if action == "advance" and row.phase == "HIGH_LEVEL_DESIGN":
        graph = normalize_scene(parse_scene(row.diagram))
        if not graph.nodes:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "empty_diagram",
                    "message": "Draw your design before moving on.",
                },
            )
        issues = graph.issues()
        if issues and not req.acknowledge_issues:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "diagram_issues",
                    "message": "Some of your diagram isn't connected.",
                    "issues": [
                        {
                            "kind": i.kind,
                            "element_id": i.element_id,
                            "message": i.message,
                        }
                        for i in issues
                    ],
                },
            )

    if text and action != "retry":
        await db.add_candidate_message(pg_conn, session_id, row.phase, text)

    next_phase = None
    if action == "advance":
        next_phase = rubric.next_phase(row.phase)
    elif action == "finish":
        next_phase = "FEEDBACK"
    await db.begin_turn(pg_conn, session_id, next_phase=next_phase)
    # Commit before publishing — the dispatcher's write must land after ours.
    await pg_conn.commit()
    await _publish(amqp_client, session_id, action, text or None)
    return model.TurnResponse(phase=next_phase or row.phase)


async def dismiss(pg_conn: PgConnection, user_id: str, session_id: str) -> dict:
    await db.delete_session(pg_conn, session_id, user_id)
    return {"ok": True}
