"""Interview phases, level expectations, and the grading rubric.

The grader scores each dimension 1-5 against the candidate's level; the letter
grade and hire signal are derived here, deterministically, so they stay
consistent across sessions and models.
"""

from dataclasses import dataclass

# Interview phases in order (matches SystemDesignPhase in contract.prisma).
PHASES = ("REQUIREMENTS", "ESTIMATION", "HIGH_LEVEL_DESIGN", "DEEP_DIVE", "FEEDBACK")

# Phases the candidate can leave with "advance". The deep dive ends when the
# interviewer (or the candidate) finishes the interview.
ADVANCEABLE_PHASES = ("REQUIREMENTS", "ESTIMATION", "HIGH_LEVEL_DESIGN")

# Time budget per phase for a 45-minute interview.
PHASE_TARGET_SECONDS = {
    "REQUIREMENTS": 6 * 60,
    "ESTIMATION": 5 * 60,
    "HIGH_LEVEL_DESIGN": 15 * 60,
    "DEEP_DIVE": 15 * 60,
}

PHASE_LABELS = {
    "REQUIREMENTS": "Requirements",
    "ESTIMATION": "Estimation",
    "HIGH_LEVEL_DESIGN": "High-Level Design",
    "DEEP_DIVE": "Deep Dive",
    "FEEDBACK": "Feedback",
}

LEVELS = ("MID", "SENIOR", "STAFF")

LEVEL_EXPECTATIONS = {
    "MID": (
        "Mid-level (L4): drives the requirements with some prompting, produces "
        "a working high-level design with the standard building blocks, and "
        "can explain the main trade-offs when asked. Depth on one or two areas "
        "is enough; gaps in scaling details are acceptable if they reason "
        "sensibly when pushed."
    ),
    "SENIOR": (
        "Senior (L5): drives the whole interview with little prompting, makes "
        "and justifies explicit trade-offs, sizes the system from their own "
        "estimates, and goes deep on the hardest parts (data model, "
        "consistency, failure modes, hot spots) without being led there."
    ),
    "STAFF": (
        "Staff (L6+): everything expected of senior, plus anticipates "
        "second-order problems (operability, migrations, cost, multi-region, "
        "evolving requirements), frames choices in terms of risk and "
        "business impact, and steers the deep dive to what matters most."
    ),
}

SCORE_ANCHORS = {
    1: "Well below the bar for this level",
    2: "Below the bar for this level",
    3: "Meets the bar for this level",
    4: "Above the bar for this level",
    5: "Exceptional for this level",
}


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    weight: float
    description: str


DIMENSIONS: tuple[Dimension, ...] = (
    Dimension(
        "requirements",
        "Requirements",
        0.15,
        "Clarifies scope and scale with good questions; states functional and "
        "non-functional requirements that fit the problem.",
    ),
    Dimension(
        "estimation",
        "Estimation",
        0.10,
        "Back-of-the-envelope math for traffic, storage, and bandwidth is "
        "sound, and the numbers inform design choices.",
    ),
    Dimension(
        "high_level_design",
        "High-Level Design",
        0.25,
        "Components and data flow satisfy the requirements; the API and data "
        "model are sensible; nothing essential is missing.",
    ),
    Dimension(
        "deep_dive",
        "Deep Dive & Trade-offs",
        0.30,
        "Goes deep on the hard parts: scaling, consistency, failure modes, "
        "bottlenecks. Explains trade-offs and alternatives with reasons.",
    ),
    Dimension(
        "communication",
        "Communication",
        0.10,
        "Explains thinking clearly, structures the discussion, and responds "
        "well to questions and hints.",
    ),
    Dimension(
        "time_management",
        "Time Management",
        0.10,
        "Moves through the phases at a sensible pace and leaves time for the "
        "deep dive.",
    ),
)

DIMENSION_KEYS = tuple(d.key for d in DIMENSIONS)

HIRE_SIGNALS = ("STRONG_HIRE", "HIRE", "LEAN_NO_HIRE", "NO_HIRE")

HIRE_SIGNAL_LABELS = {
    "STRONG_HIRE": "Strong Hire",
    "HIRE": "Hire",
    "LEAN_NO_HIRE": "Lean No Hire",
    "NO_HIRE": "No Hire",
}


# (minimum weighted score, letter), highest first. 3.0 is "meets the bar".
_LETTER_FLOORS = (
    (4.4, "A+"),
    (3.9, "A"),
    (3.6, "A-"),
    (3.3, "B+"),
    (3.0, "B"),
    (2.7, "B-"),
    (2.4, "C+"),
    (2.1, "C"),
    (1.8, "C-"),
    (1.5, "D"),
)


def next_phase(phase: str) -> str | None:
    """The phase after `phase`, or None past the end / for unknown phases."""
    if phase not in PHASES:
        return None
    i = PHASES.index(phase)
    return PHASES[i + 1] if i + 1 < len(PHASES) else None


def _clamped(scores: dict[str, int]) -> dict[str, int]:
    return {d.key: min(5, max(1, int(scores.get(d.key) or 1))) for d in DIMENSIONS}


def weighted_score(scores: dict[str, int]) -> float:
    """Weighted 1-5 average over every rubric dimension. A missing score
    counts as 1 (the dimension wasn't demonstrated); others clamp to 1-5."""
    clamped = _clamped(scores)
    return sum(d.weight * clamped[d.key] for d in DIMENSIONS)


def letter_grade(score: float) -> str:
    """Map a weighted 1-5 score onto A+ .. F. 3.0 ("meets the bar") is a B."""
    # Rounded so float noise in the weighted sum can't drop a boundary score.
    score = round(score, 6)
    for floor, letter in _LETTER_FLOORS:
        if score >= floor:
            return letter
    return "F"


def hire_signal(scores: dict[str, int]) -> str:
    """Strong Hire / Hire / Lean No Hire / No Hire from the weighted score,
    with a floor: a dimension well below the bar blocks a hire."""
    clamped = _clamped(scores)
    score = round(weighted_score(clamped), 6)
    lowest = min(clamped.values())
    if score >= 3.9 and lowest >= 3:
        return "STRONG_HIRE"
    if score >= 3.0 and lowest >= 2:
        return "HIRE"
    if score >= 2.4:
        return "LEAN_NO_HIRE"
    return "NO_HIRE"
