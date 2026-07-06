import unittest
from pathlib import Path

from app.services.excel_import.candidates import ImportCandidateService
from app.services.excel_import.pipeline import ExcelImportPipeline

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


class _WarningCollector:
    """Minimal stand-in for a SQLAlchemy session that only records add() calls."""

    def __init__(self) -> None:
        self.added = []

    def add(self, instance) -> None:
        self.added.append(instance)


class HeaderCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = ExcelImportPipeline(CONFIG_DIR)
        cls.candidates = ImportCandidateService(CONFIG_DIR)

    def test_first_value_prefers_new_headers_and_falls_back(self) -> None:
        values = {"Geography": "TR", "Coğrafya": None}
        self.assertEqual(self.candidates._first_value(values, "Geography", "Coğrafya"), "TR")
        values = {"Coğrafya": "USA"}
        self.assertEqual(self.candidates._first_value(values, "Geography", "Coğrafya"), "USA")
        self.assertIsNone(self.candidates._first_value({}, "Geography", "Coğrafya"))

    def test_row_to_dict_keeps_first_non_empty_for_duplicate_headers(self) -> None:
        # The PoC sheet repeats "Status" in two side-by-side blocks; the empty
        # right-hand block must not erase the left-hand value.
        headers = ["Startup", "Status", "Notes", "Status"]
        row = ("Wyseye", "PoC In Progress", None, None)
        values = self.pipeline._row_to_dict(row, headers, preserve_raw=False)
        self.assertEqual(values["Status"], "PoC In Progress")

    def test_numbered_process_status_values_resolve(self) -> None:
        expectations = {
            "1- Info": "INFORMATION_RECEIVED",
            "2- Contacted / Positive": "MEETING_HELD",
            "2- Contacted / Negative": "NOT_A_FIT",
            "3- Planned for the future": "IN_PROGRESS",
            "4- NDA / Contract": "NDA",
            "5- PoC In Progress": "POC_IN_PROGRESS",
            "6- PoC Successful": "POC_SUCCESSFUL",
            "6- PoC Failed": "POC_FAILED",
            "7- Partnered": "PARTNERED",
        }
        for raw, expected in expectations.items():
            self.assertEqual(self.candidates._status_code(raw, "company_status"), expected, raw)

    def test_english_network_relationship_values_resolve(self) -> None:
        expectations = {
            "Known contact": "ACQUAINTANCE",
            "Close relationship": "CLOSE_RELATIONSHIP",
            "No close relationship": "NO_CLOSE_RELATIONSHIP",
            "Info": "INFORMATION_ONLY",
            "Borusan Ventures investor": "BORUSAN_VENTURES_INVESTOR",
            "Borusan Group investor": "BORUSAN_GROUP_INVESTOR",
        }
        for raw, expected in expectations.items():
            self.assertEqual(self.candidates._status_code(raw, "network_relationship"), expected, raw)

    def test_english_fit_columns_map_to_borusan_companies(self) -> None:
        columns = self.candidates._borusan_fit_columns()
        self.assertEqual(columns.get("Automotive"), "OTO")
        self.assertEqual(columns.get("Energy"), "ENERGY")
        self.assertEqual(columns.get("Port"), "PORT")
        # Legacy Turkish columns keep working.
        self.assertEqual(columns.get("Oto"), "OTO")
        self.assertEqual(columns.get("Enerji"), "ENERGY")
        self.assertEqual(columns.get("Liman"), "PORT")

    def test_required_columns_accept_alternative_header_names(self) -> None:
        mapping = {"required_columns": [["Etkinlik Adı", "Event Name"], ["Lokasyon", "Location"]]}
        collector = _WarningCollector()
        batch = type("Batch", (), {"id": None})()
        self.pipeline._validate_required_columns(collector, batch, "Events", mapping, ["Event Name", "Location"])
        self.assertEqual(collector.added, [])
        self.pipeline._validate_required_columns(collector, batch, "Events", mapping, ["Something Else"])
        self.assertEqual(len(collector.added), 2)
        codes = {warning.code for warning in collector.added}
        self.assertEqual(codes, {"MISSING_REQUIRED_COLUMN"})

    def test_column_type_mismatch_detected_for_shifted_columns(self) -> None:
        collector = _WarningCollector()
        batch = type("Batch", (), {"id": None})()
        mapping = {"header_row": 1, "first_data_row": 2}
        headers = ["Last Contact", "Startup"]
        rows = [tuple(headers)] + [(f"Some text {i}", f"Startup {i}") for i in range(6)]
        self.pipeline._validate_column_types(collector, batch, "Startup Library", "STARTUP_LIBRARY", mapping, headers, rows)
        self.assertEqual(len(collector.added), 1)
        self.assertEqual(collector.added[0].code, "COLUMN_TYPE_MISMATCH")

    def test_column_type_check_passes_for_real_dates(self) -> None:
        collector = _WarningCollector()
        batch = type("Batch", (), {"id": None})()
        mapping = {"header_row": 1, "first_data_row": 2}
        headers = ["Last Contact", "Startup"]
        rows = [tuple(headers)] + [(f"2024-0{i + 1}-01", f"Startup {i}") for i in range(6)]
        self.pipeline._validate_column_types(collector, batch, "Startup Library", "STARTUP_LIBRARY", mapping, headers, rows)
        self.assertEqual(collector.added, [])

    def test_unmapped_columns_generate_warning(self) -> None:
        collector = _WarningCollector()
        batch = type("Batch", (), {"id": None})()
        self.pipeline._warn_unmapped_columns(
            collector, batch, "Startup Library", "STARTUP_LIBRARY", ["Startup", "Mystery Column"]
        )
        self.assertEqual(len(collector.added), 1)
        self.assertEqual(collector.added[0].code, "UNMAPPED_COLUMN")
        self.assertIn("Mystery Column", collector.added[0].message)


if __name__ == "__main__":
    unittest.main()
