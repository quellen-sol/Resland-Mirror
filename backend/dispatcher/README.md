# dispatcher

Resland's AMQP consumers and LangGraph agents: the resume parser, bullet coaching,
tailoring, and the system design interviewer, brief writer and grader. It also holds the
PDF and DOCX layout parsers. On startup it declares the RabbitMQ topology and creates the
LangGraph checkpoint tables in the `langgraph` schema.

```bash
uv run dispatcher
uv run pytest --cov
```

The [root README](../../README.md) walks through each agent's flow, and
[`AGENTS.md`](../../AGENTS.md) covers the local setup and test database.
