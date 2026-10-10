"""The user's memory bank rules, shared by everything that reads or writes it:
the dispatcher's interviewing agents, the API's /memory endpoints, and the
personal MCP server.

Facts the user gives in interview answers outlive the run, so later tailor and
suggestion sessions read them back instead of asking again. Users review and
edit the bank on the /memory page.

The prompt text avoids em dashes on purpose (see writing.py).
"""

# Keep in sync with frontend/lib/memory.ts. The whole bank goes into every
# run's context, so the cap bounds what it adds to each LLM call.
MAX_MEMORY_FACTS = 200
MAX_TOPIC_CHARS = 120
MAX_FACT_CHARS = 500

MEMORY_RULES = """Memory:
- memory holds facts the user told you in earlier sessions, each with an id
  and a topic naming the job, project, or preference it's about. Treat them
  like answers the user just gave: use them in the writing, and never ask for
  something memory already answers.
- Save what you learn. After the user answers your questions or gives
  feedback that adds or corrects facts about their work, call remember_facts
  with each lasting fact, alongside your next tool call:
  - One fact per entry, self-contained, so someone reading only that entry
    knows which work it describes. Keep the user's numbers and names.
  - topic: "<title> at <company>" exactly as the profile shows the job, a
    project's name, "Preferences" for how they want their resume written, or
    "General".
  - Save facts about the user's work and lasting preferences. Don't save
    anything about this job posting, your own guesses or wording, questions
    the user skipped, or what the profile already says.
  - When an answer corrects or adds to a fact already in memory, pass that
    fact's id as replaces_id with the full updated fact rather than adding a
    second one."""
