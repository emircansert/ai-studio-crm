import unittest
from types import SimpleNamespace

from app.core.section_access import (
    ACCESS_FULL,
    ACCESS_HIDDEN,
    ACCESS_VIEW,
    access_allows,
    default_access_for_user,
    match_section_for_path,
    required_access_for_method,
    validate_section_access_map,
)


class SectionAccessTests(unittest.TestCase):
    def test_safe_defaults_are_role_aware(self) -> None:
        self.assertEqual(default_access_for_user(SimpleNamespace(role="USER")), ACCESS_HIDDEN)
        self.assertEqual(default_access_for_user(SimpleNamespace(role="ADMIN")), ACCESS_FULL)

    def test_read_and_write_method_requirements(self) -> None:
        self.assertEqual(required_access_for_method("GET"), ACCESS_VIEW)
        self.assertEqual(required_access_for_method("HEAD"), ACCESS_VIEW)
        self.assertEqual(required_access_for_method("POST"), ACCESS_FULL)
        self.assertEqual(required_access_for_method("PATCH"), ACCESS_FULL)

    def test_access_levels_allow_expected_actions(self) -> None:
        self.assertFalse(access_allows(ACCESS_HIDDEN, ACCESS_VIEW))
        self.assertTrue(access_allows(ACCESS_VIEW, ACCESS_VIEW))
        self.assertFalse(access_allows(ACCESS_VIEW, ACCESS_FULL))
        self.assertTrue(access_allows(ACCESS_FULL, ACCESS_VIEW))
        self.assertTrue(access_allows(ACCESS_FULL, ACCESS_FULL))

    def test_api_path_mapping_prefers_specific_admin_paths(self) -> None:
        self.assertEqual(match_section_for_path("/api/v1/organizations").key, "STARTUP_LIBRARY")
        self.assertEqual(match_section_for_path("/api/v1/organizations/abc/notes").key, "STARTUP_LIBRARY")
        self.assertEqual(match_section_for_path("/api/v1/opportunities/abc/stage").key, "POC_PIPELINE")
        self.assertEqual(match_section_for_path("/api/v1/opportunities/abc/documents").key, "POC_PIPELINE")
        self.assertEqual(match_section_for_path("/api/v1/admin/leaderboard/reset").key, "LEADERBOARD_ADMIN")
        self.assertEqual(match_section_for_path("/api/v1/admin/champion-activities").key, "CHAMPION_PROGRAM")
        self.assertIsNone(match_section_for_path("/api/v1/admin/users"))

    def test_unknown_or_invalid_access_payload_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_section_access_map({"UNKNOWN": ACCESS_VIEW})
        with self.assertRaises(ValueError):
            validate_section_access_map({"STARTUP_LIBRARY": "WRITE"})


if __name__ == "__main__":
    unittest.main()
