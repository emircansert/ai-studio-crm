import argparse
import json
from pathlib import Path

from app.services.excel_import.pipeline import ExcelImportPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile an Excel workbook without committing CRM records.")
    parser.add_argument("workbook", type=Path, help="Path to an .xlsx workbook")
    parser.add_argument("--config-dir", type=Path, default=Path("..") / "config")
    args = parser.parse_args()

    pipeline = ExcelImportPipeline(args.config_dir)
    profile = pipeline.profile_workbook_file(args.workbook)
    print(json.dumps({"filename": profile.filename, "sheets": profile.sheets}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
