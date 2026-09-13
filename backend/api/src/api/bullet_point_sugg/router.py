from fastapi import APIRouter

from ..auth import Auth0UserId
from ..deps import PgConnection
from . import model, service

router = APIRouter(prefix="/bullets")


@router.post("/suggestions", response_model=model.StartSuggestionResponse)
def start_suggestion(
    req: model.StartSuggestionRequest, user_id: Auth0UserId, pg_conn: PgConnection
):
    return service.start_suggestion(req=req, user_id=user_id, pg_conn=pg_conn)


@router.get("/suggestions/{session_id}", response_model=model.SuggestionStatusResponse)
def get_suggestion(user_id: Auth0UserId, req: model.GetSuggestionRequest):
    return service.get_suggestion(user_id=user_id, session_id=req.session_id)


@router.post("/suggestions/{session_id}/answer")
def answer_suggestion(user_id: Auth0UserId, req: model.AnswerRequest):
    return service.answer_suggestion(user_id=user_id, req=req)


@router.post("/suggestions/{session_id}/accept")
def accept_suggestion(user_id: Auth0UserId, session_id: str):
    return service.accept_suggestion(user_id=user_id, session_id=session_id)


@router.post("/suggestions/{session_id}/dismiss")
def dismiss_suggestion(user_id: Auth0UserId, session_id: str):
    return service.dismiss_suggestion(user_id=user_id, session_id=session_id)
