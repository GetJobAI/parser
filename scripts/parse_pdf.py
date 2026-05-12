#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.pipeline.resume_pipeline import ResumePipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse a resume PDF locally without database dependencies."
    )
    parser.add_argument("file", type=Path, help="Path to a .pdf file")
    parser.add_argument(
        "--parser-version",
        default="v1",
        help="Parser version label stored in metadata (default: v1)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output report path (.md). Default: <pdf_stem>.parsed.md next to input file",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    file_path: Path = args.file

    if not file_path.exists():
        raise SystemExit(f"File not found: {file_path}")
    if file_path.suffix.lower() != ".pdf":
        raise SystemExit("Only .pdf files are supported by this script.")

    pipeline = ResumePipeline(parser_version=args.parser_version)
    content, report = pipeline.parse(
        file_bytes=file_path.read_bytes(),
        filename=file_path.name,
        mime_type="application/pdf",
    )

    output_path: Path = args.output or file_path.with_name(f"{file_path.stem}.parsed.md")
    markdown_report = _to_markdown(
        source_file=file_path,
        parser_version=args.parser_version,
        content_json=json.dumps(content.model_dump(), indent=2, ensure_ascii=False),
        report_json=json.dumps(report.model_dump(), indent=2, ensure_ascii=False),
    )
    output_path.write_text(markdown_report, encoding="utf-8")

    print("=== Parsed Content ===")
    print(json.dumps(content.model_dump(), indent=2, ensure_ascii=False))
    print("\n=== Quality Report ===")
    print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
    print(f"\nMarkdown report saved to: {output_path}")
    return 0


def _to_markdown(
    *,
    source_file: Path,
    parser_version: str,
    content_json: str,
    report_json: str,
) -> str:
    return (
        f"# Resume Parse Report\n\n"
        f"- Source file: `{source_file}`\n"
        f"- Parser version: `{parser_version}`\n\n"
        f"## Parsed Content\n\n"
        f"```json\n{content_json}\n```\n\n"
        f"## Quality Report\n\n"
        f"```json\n{report_json}\n```\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
