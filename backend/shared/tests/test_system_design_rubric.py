"""System design rubric — phase order, weighted score, letter grade and hire
signal mapping. Pure functions, no infrastructure.

Run: .venv/bin/python -m unittest backend.shared.tests.test_system_design_rubric -v
"""

import math
import unittest

from shared.system_design import rubric


def scores(value: int, **over) -> dict[str, int]:
    out = {key: value for key in rubric.DIMENSION_KEYS}
    out.update(over)
    return out


class Phases(unittest.TestCase):
    def test_next_phase_walks_the_interview_in_order(self):
        self.assertEqual(rubric.next_phase("REQUIREMENTS"), "ESTIMATION")
        self.assertEqual(rubric.next_phase("ESTIMATION"), "HIGH_LEVEL_DESIGN")
        self.assertEqual(rubric.next_phase("HIGH_LEVEL_DESIGN"), "DEEP_DIVE")
        self.assertEqual(rubric.next_phase("DEEP_DIVE"), "FEEDBACK")

    def test_nothing_after_feedback_or_unknown(self):
        self.assertIsNone(rubric.next_phase("FEEDBACK"))
        self.assertIsNone(rubric.next_phase("LUNCH"))

    def test_every_timed_phase_has_a_label(self):
        for phase in rubric.PHASES:
            self.assertIn(phase, rubric.PHASE_LABELS)
        self.assertNotIn("FEEDBACK", rubric.PHASE_TARGET_SECONDS)


class WeightedScore(unittest.TestCase):
    def test_weights_sum_to_one(self):
        self.assertTrue(math.isclose(sum(d.weight for d in rubric.DIMENSIONS), 1.0))

    def test_uniform_scores_return_that_score(self):
        self.assertAlmostEqual(rubric.weighted_score(scores(3)), 3.0)
        self.assertAlmostEqual(rubric.weighted_score(scores(5)), 5.0)

    def test_missing_dimension_counts_as_one(self):
        partial = scores(5)
        del partial["deep_dive"]
        # deep_dive carries 0.30 of the weight.
        self.assertAlmostEqual(rubric.weighted_score(partial), 0.7 * 5 + 0.3 * 1)

    def test_out_of_range_scores_are_clamped(self):
        self.assertAlmostEqual(rubric.weighted_score(scores(9)), 5.0)
        self.assertAlmostEqual(rubric.weighted_score(scores(0)), 1.0)

    def test_weights_matter(self):
        heavy = rubric.weighted_score(scores(3, deep_dive=5))
        light = rubric.weighted_score(scores(3, estimation=5))
        self.assertGreater(heavy, light)


class LetterGrade(unittest.TestCase):
    def test_meets_the_bar_is_a_b(self):
        self.assertEqual(rubric.letter_grade(3.0), "B")

    def test_boundaries(self):
        cases = [
            (5.0, "A+"),
            (4.4, "A+"),
            (4.39, "A"),
            (3.9, "A"),
            (3.6, "A-"),
            (3.3, "B+"),
            (2.99, "B-"),
            (2.7, "B-"),
            (2.4, "C+"),
            (2.1, "C"),
            (1.8, "C-"),
            (1.5, "D"),
            (1.49, "F"),
            (1.0, "F"),
        ]
        for score, grade in cases:
            with self.subTest(score=score):
                self.assertEqual(rubric.letter_grade(score), grade)


class HireSignal(unittest.TestCase):
    def test_strong_hire(self):
        self.assertEqual(rubric.hire_signal(scores(4)), "STRONG_HIRE")

    def test_meets_bar_is_hire(self):
        self.assertEqual(rubric.hire_signal(scores(3)), "HIRE")

    def test_one_dimension_well_below_blocks_hire(self):
        self.assertEqual(rubric.hire_signal(scores(4, estimation=1)), "LEAN_NO_HIRE")

    def test_strong_hire_needs_every_dimension_at_bar(self):
        self.assertEqual(rubric.hire_signal(scores(5, communication=2)), "HIRE")

    def test_below_bar(self):
        self.assertEqual(rubric.hire_signal(scores(2)), "NO_HIRE")
        self.assertEqual(rubric.hire_signal(scores(3, deep_dive=2)), "LEAN_NO_HIRE")

    def test_signals_are_known(self):
        for value in range(1, 6):
            self.assertIn(rubric.hire_signal(scores(value)), rubric.HIRE_SIGNALS)


if __name__ == "__main__":
    unittest.main()
