"""The user's memory bank, as the interviewing agents see it.

Facts the user gives in interview answers outlive the run: the agent saves
them with remember_facts, and later tailor and suggestion runs read them back
alongside the profile instead of asking again. Users review and edit the bank
on the /memory page.

The limits and prompt rules live in shared.memory, which the API's /memory
endpoints and the personal MCP server use too.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from langchain.tools import tool
from pydantic import BaseModel
from shared.memory import (  # noqa: F401 - the agents and db_ops read them here
    MAX_FACT_CHARS,
    MAX_MEMORY_FACTS,
    MAX_TOPIC_CHARS,
    MEMORY_RULES,
)


class MemoryFact(BaseModel):
    id: int
    topic: str
    content: str


class NewMemoryFact(BaseModel):
    topic: str
    content: str
    # A bank fact this one corrects or extends; it's rewritten in place.
    replaces_id: int | None = None


@dataclass
class MemorySaveResult:
    # Facts now in the bank (newly stored, rewritten, or already there).
    saved: list[MemoryFact] = field(default_factory=list)
    # New facts turned away because the bank is at MAX_MEMORY_FACTS.
    full: int = 0


@dataclass
class MemoryBank:
    """The bank as one run sees it: the facts at run start, and how to store
    new ones (db_ops.save_memory_facts bound to the user and source)."""

    facts: list[MemoryFact]
    save: Callable[[list[NewMemoryFact]], MemorySaveResult]


def check_new_facts(facts: list[NewMemoryFact]) -> list[str]:
    """Problems that keep facts out of the bank, one per bad entry."""
    problems = []
    for n, fact in enumerate(facts, start=1):
        topic, content = fact.topic.strip(), fact.content.strip()
        if not topic or not content:
            problems.append(f"Fact {n} needs both a topic and content.")
        elif len(topic) > MAX_TOPIC_CHARS:
            problems.append(
                f"Fact {n}'s topic is over {MAX_TOPIC_CHARS} characters; shorten it."
            )
        elif len(content) > MAX_FACT_CHARS:
            problems.append(
                f"Fact {n} is over {MAX_FACT_CHARS} characters; split it into "
                "smaller facts."
            )
    return problems


def make_remember_tool(bank: MemoryBank):
    """The remember_facts tool, bound to one run's bank."""

    @tool
    def remember_facts(facts: list[NewMemoryFact]):
        """Save lasting facts the user told you about their work, or their
        preferences, to their memory bank so later sessions don't ask again.
        Set replaces_id to rewrite a fact already in memory."""
        if not facts:
            return "No facts given, so nothing was saved."
        # Nothing is stored until the whole batch is valid, so the batch can
        # be resent as-is once fixed without duplicating the good entries.
        if problems := check_new_facts(facts):
            return "Nothing was saved. " + " ".join(problems)
        cleaned = [
            fact.model_copy(
                update={"topic": fact.topic.strip(), "content": fact.content.strip()}
            )
            for fact in facts
        ]
        try:
            result = bank.save(cleaned)
        except Exception as e:
            print(f"Failed to save memory facts: {e}")
            return "Couldn't save to memory right now. Carry on without it."
        notes = []
        if result.saved:
            ids = ", ".join(str(fact.id) for fact in result.saved)
            notes.append(f"Saved to memory as ids {ids}.")
        if result.full:
            notes.append(
                f"{result.full} new fact(s) weren't saved because memory is "
                f"full ({MAX_MEMORY_FACTS} facts). Use replaces_id to update an "
                "outdated fact instead."
            )
        return " ".join(notes)

    return remember_facts
