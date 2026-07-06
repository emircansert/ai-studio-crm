import unittest

from fastapi import HTTPException

from app.api.v1.endpoints.opportunities import normalize_poc_stage


class PocPipelineStageTests(unittest.TestCase):
    def test_canonical_stages_are_preserved(self) -> None:
        for stage in ["IDEA", "SCOUTING", "SHORT_LISTING", "POC", "POST_POC"]:
            self.assertEqual(normalize_poc_stage(stage), stage)

    def test_legacy_stages_map_to_funnel(self) -> None:
        self.assertEqual(normalize_poc_stage("DISCOVERY"), "SCOUTING")
        self.assertEqual(normalize_poc_stage("EVALUATION"), "SHORT_LISTING")
        self.assertEqual(normalize_poc_stage("POC_ACTIVE"), "POC")
        self.assertEqual(normalize_poc_stage("COMPLETED"), "POST_POC")

    def test_unknown_stage_is_rejected_for_new_updates(self) -> None:
        with self.assertRaises(HTTPException):
            normalize_poc_stage("NOT_A_PIPELINE_STAGE")


if __name__ == "__main__":
    unittest.main()
