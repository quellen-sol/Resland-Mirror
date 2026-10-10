"""Prompt rules shared by the agents that write resume bullets.

The prompt text avoids em dashes on purpose: models mirror the punctuation
they're shown, and the style rules below ban them in the output.
"""

BULLET_WRITING_RULES = """Honesty:
- Never invent metrics, tools, employers, scope, or outcomes. Facts the user
  gives you in their answers count as stated; anything else does not.
- Make the framing stronger, never the claim. "Helped build" becomes "built"
  only if the user says they built it; a team result stays a team result
  unless the user says they drove it.
- No placeholders such as "X%" or "[number]". Bullets go straight onto the
  resume, so when a number is missing, write the bullet without it.
- When the user says they haven't done something, leave it out. Don't bend
  nearby work to cover the gap.

Style:
- Each bullet says what the user did, how, and what came of it (a result,
  the scale, or who relied on it), in 1-2 lines. Lead with the part that
  matters most to the reader, start with a strong action verb, and keep the
  original bullet's tense and voice.
- Write like a person, not a model. No em dashes (use commas or periods). No
  AI vocabulary: spearheaded, leveraged, orchestrated, fostered, delve,
  robust, seamless, dynamic, results-driven, passionate, cutting-edge. No
  three-adjective stacks before a noun. Prefer concrete verbs that name the
  act (built, shipped, cut, doubled) over verbs that could appear on any
  resume in any industry.
- Cut filler and process detail the reader doesn't need, so the work that
  matters stands out."""
