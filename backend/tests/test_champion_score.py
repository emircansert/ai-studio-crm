import unittest

from app.services.champion_score import category_score, next_action_hint


class ChampionScoreRulesTest(unittest.TestCase):
    def test_vision_strategy_thresholds(self) -> None:
        self.assertEqual(category_score("VISION_STRATEGY", 0), 0)
        self.assertEqual(category_score("VISION_STRATEGY", 1), 50)
        self.assertEqual(category_score("VISION_STRATEGY", 2), 100)

    def test_ecosystem_library_thresholds(self) -> None:
        self.assertEqual(category_score("ECOSYSTEM_LIBRARY", 0), 0)
        self.assertEqual(category_score("ECOSYSTEM_LIBRARY", 1), 50)
        self.assertEqual(category_score("ECOSYSTEM_LIBRARY", 7), 50)
        self.assertEqual(category_score("ECOSYSTEM_LIBRARY", 8), 100)

    def test_startup_scouting_thresholds(self) -> None:
        self.assertEqual(category_score("STARTUP_SCOUTING", 0), 0)
        self.assertEqual(category_score("STARTUP_SCOUTING", 4), 50)
        self.assertEqual(category_score("STARTUP_SCOUTING", 5), 100)

    def test_event_and_training_thresholds(self) -> None:
        self.assertEqual(category_score("COMMUNICATION_EVENT", 1), 0)
        self.assertEqual(category_score("COMMUNICATION_EVENT", 2), 50)
        self.assertEqual(category_score("COMMUNICATION_EVENT", 5), 100)
        self.assertEqual(category_score("TRAINING", 0), 0)
        self.assertEqual(category_score("TRAINING", 1), 100)

    def test_next_action_hint_returns_rule_based_guidance(self) -> None:
        self.assertIn("1 more", next_action_hint("VISION_STRATEGY", 1) or "")
        self.assertIn("3 more", next_action_hint("ECOSYSTEM_LIBRARY", 5) or "")


if __name__ == "__main__":
    unittest.main()
