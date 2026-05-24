from __future__ import annotations

from app.job.html import HTMLJobExtractor
from app.job.parser import JobPostingParser
from app.job.quality import JobPostingQualityChecker, JobPostingQualityReport
from app.schemas.job_posting import JobPostingContent


class JobPostingPipeline:
    def __init__(self, *, parser_version: str) -> None:
        self._parser_version = parser_version
        self._html_extractor = HTMLJobExtractor()
        self._parser = JobPostingParser()
        self._quality_checker = JobPostingQualityChecker()

    def parse(
        self,
        *,
        html: str | None = None,
        text: str | None = None,
        source_url: str | None = None,
    ) -> tuple[JobPostingContent, JobPostingQualityReport]:
        content = JobPostingContent.build_processing(
            parser_version=self._parser_version,
            source_url=source_url,
            html_provided=bool(html),
        )

        try:
            extracted_text = ""
            title_candidates: list[str] = []
            meta_title: str | None = None
            meta_description: str | None = None
            structured_data = None
            salary_hint: str | None = None

            if html:
                extracted = self._html_extractor.extract(html)
                content.meta.extraction_method = "html_rules"
                content.meta.warnings.extend(extracted.warnings)
                extracted_text = extracted.text
                title_candidates = extracted.title_candidates
                meta_title = extracted.meta_title
                meta_description = extracted.meta_description
                structured_data = extracted.structured_data
                salary_hint = extracted.salary_hint
            elif text:
                content.meta.extraction_method = "plain_text"
                extracted_text = text.strip()
            else:
                raise ValueError("Either html or text must be provided.")

            content = self._parser.parse(
                content=content,
                text=extracted_text,
                title_candidates=title_candidates,
                meta_title=meta_title,
                meta_description=meta_description,
                structured_data=structured_data,
                salary_hint=salary_hint,
            )

            quality_report = self._quality_checker.evaluate(content)
            content.meta.partial_parse = quality_report.partial_parse
            content.meta.warnings.extend(quality_report.warnings)
            content.meta.warnings = list(dict.fromkeys(content.meta.warnings))
            content.meta.parse_status = "completed"
            content.meta.parse_error = None
            return content, quality_report
        except Exception as exc:
            content.meta.parse_status = "failed"
            content.meta.parse_error = str(exc)
            content.meta.partial_parse = True
            content.meta.warnings = list(dict.fromkeys(content.meta.warnings + ["Job posting parsing failed."]))
            return content, JobPostingQualityReport(
                warnings=content.meta.warnings,
                partial_parse=True,
                major_sections_found=[],
            )
