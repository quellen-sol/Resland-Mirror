"""The curated problem bank and the interviewer brief shape.

Each bank entry carries a hand-checked brief (bank.json) — scale answers,
expected requirements, a reference design, deep-dive topics — so grading is
consistent across sessions. Briefs generated from a job posting use the same
InterviewBrief shape.
"""

import json
import random
from dataclasses import asdict, dataclass, field
from functools import cache
from pathlib import Path

BANK_PATH = Path(__file__).with_name("bank.json")

DIFFICULTIES = ("EASY", "MEDIUM", "HARD")


@dataclass(frozen=True)
class Clarification:
    topic: str
    answer: str


@dataclass(frozen=True)
class RefComponent:
    id: str
    kind: str
    label: str
    purpose: str


@dataclass(frozen=True)
class RefConnection:
    source: str
    target: str
    label: str = ""


@dataclass(frozen=True)
class InterviewBrief:
    """The interviewer's private notes for one problem. Only `title` and
    `prompt` are shown to the candidate before the interview is graded."""

    title: str
    prompt: str
    clarifications: tuple[Clarification, ...] = ()
    functional_requirements: tuple[str, ...] = ()
    non_functional_requirements: tuple[str, ...] = ()
    estimation_notes: tuple[str, ...] = ()
    reference_components: tuple[RefComponent, ...] = ()
    reference_connections: tuple[RefConnection, ...] = ()
    deep_dive_topics: tuple[str, ...] = ()
    pitfalls: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "InterviewBrief":
        def strings(key: str) -> tuple[str, ...]:
            return tuple(str(v) for v in data.get(key) or [])

        return cls(
            title=str(data.get("title") or ""),
            prompt=str(data.get("prompt") or ""),
            clarifications=tuple(
                Clarification(topic=c["topic"], answer=c["answer"])
                for c in data.get("clarifications") or []
            ),
            functional_requirements=strings("functional_requirements"),
            non_functional_requirements=strings("non_functional_requirements"),
            estimation_notes=strings("estimation_notes"),
            reference_components=tuple(
                RefComponent(
                    id=c["id"], kind=c["kind"], label=c["label"], purpose=c["purpose"]
                )
                for c in data.get("reference_components") or []
            ),
            reference_connections=tuple(
                RefConnection(
                    source=c["source"], target=c["target"], label=c.get("label") or ""
                )
                for c in data.get("reference_connections") or []
            ),
            deep_dive_topics=strings("deep_dive_topics"),
            pitfalls=strings("pitfalls"),
        )

    @classmethod
    def from_json(cls, raw: str) -> "InterviewBrief":
        return cls.from_dict(json.loads(raw))


@dataclass(frozen=True)
class BankProblem:
    id: str
    title: str
    difficulty: str
    summary: str
    brief: InterviewBrief
    tags: tuple[str, ...] = field(default=())


@cache
def load_bank() -> dict[str, BankProblem]:
    """Every bank problem keyed by id, in file order."""
    data = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    problems: dict[str, BankProblem] = {}
    for entry in data["problems"]:
        # The title lives once on the entry; the brief carries a copy so a
        # brief is self-contained wherever it travels.
        brief = InterviewBrief.from_dict({**entry["brief"], "title": entry["title"]})
        problems[entry["id"]] = BankProblem(
            id=entry["id"],
            title=entry["title"],
            difficulty=entry["difficulty"],
            summary=entry["summary"],
            brief=brief,
            tags=tuple(entry.get("tags") or ()),
        )
    return problems


def list_problems() -> list[BankProblem]:
    return list(load_bank().values())


def get_problem(problem_id: str) -> BankProblem | None:
    return load_bank().get(problem_id)


def pick_random(
    exclude: set[str] | frozenset[str] = frozenset(),
    rng: random.Random | None = None,
) -> BankProblem:
    """A random problem, preferring ones not in `exclude` (e.g. problems the
    user already practiced). Falls back to the whole bank once every problem
    has been seen."""
    rng = rng or random.Random()
    problems = list_problems()
    fresh = [p for p in problems if p.id not in exclude]
    return rng.choice(fresh or problems)
