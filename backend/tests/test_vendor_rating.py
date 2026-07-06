import unittest

from app.api.v1.endpoints.vendors import RATING_WEIGHTS, VENDOR_STATUSES, weighted_score
from app.core.section_access import SECTION_BY_KEY, match_section_for_path


class VendorRatingTests(unittest.TestCase):
    def test_weights_total_one_hundred_percent(self) -> None:
        self.assertAlmostEqual(sum(RATING_WEIGHTS.values()), 1.0)
        self.assertEqual(RATING_WEIGHTS["quality_score"], 0.35)
        self.assertEqual(RATING_WEIGHTS["reliability_score"], 0.25)
        self.assertEqual(RATING_WEIGHTS["pricing_score"], 0.20)
        self.assertEqual(RATING_WEIGHTS["borusan_fit_score"], 0.20)

    def test_weighted_score_bounds(self) -> None:
        self.assertAlmostEqual(weighted_score(5, 5, 5, 5), 5.0)
        self.assertAlmostEqual(weighted_score(1, 1, 1, 1), 1.0)

    def test_weighted_score_example(self) -> None:
        # 5*0.35 + 4*0.25 + 3*0.20 + 2*0.20 = 1.75 + 1.0 + 0.6 + 0.4 = 3.75
        self.assertAlmostEqual(weighted_score(5, 4, 3, 2), 3.75)

    def test_quality_weighs_more_than_pricing(self) -> None:
        high_quality = weighted_score(5, 3, 1, 3)
        high_pricing = weighted_score(1, 3, 5, 3)
        self.assertGreater(high_quality, high_pricing)

    def test_vendor_statuses_non_empty(self) -> None:
        self.assertIn("PROSPECT", VENDOR_STATUSES)


class VendorSectionAccessTests(unittest.TestCase):
    def test_vendor_api_paths_map_to_vendor_library_section(self) -> None:
        for path in (
            "/api/v1/vendors",
            "/api/v1/vendors/00000000-0000-0000-0000-000000000000",
            "/api/v1/vendors/00000000-0000-0000-0000-000000000000/my-rating",
        ):
            section = match_section_for_path(path)
            self.assertIsNotNone(section, path)
            self.assertEqual(section.key, "VENDOR_LIBRARY", path)

    def test_vendor_library_section_registered(self) -> None:
        section = SECTION_BY_KEY["VENDOR_LIBRARY"]
        self.assertFalse(section.admin_only)
        self.assertIn("/api/v1/vendors", section.api_prefixes)


if __name__ == "__main__":
    unittest.main()
