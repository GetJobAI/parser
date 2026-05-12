from __future__ import annotations

from app.detectors.boundaries import SectionedDocument, build_section_map
from app.detectors.section_detector import detect_section_headers
from app.extractors.docx_extractor import DOCXExtractor
from app.extractors.pdf_extractor import PDFExtractor
from app.parsers.certifications_parser import CertificationsParser
from app.parsers.contact_parser import ContactParser
from app.parsers.education_parser import EducationParser
from app.parsers.experience_parser import ExperienceParser
from app.parsers.generic_list_parser import GenericListParser
from app.parsers.languages_parser import LanguagesParser
from app.parsers.projects_parser import ProjectsParser
from app.parsers.skills_parser import SkillsParser
from app.parsers.summary_parser import SummaryParser
from app.preprocess.cleaner import preprocess_blocks
from app.preprocess.layout import detect_layout_and_reorder
from app.quality.checker import QualityChecker, QualityReport
from app.quality.fallback import FallbackManager
from app.schemas.content import ResumeContent, TextBlock


class ResumePipeline:
    def __init__(self, *, parser_version: str) -> None:
        self._parser_version = parser_version
        self._pdf_extractor = PDFExtractor()
        self._docx_extractor = DOCXExtractor()
        self._contact_parser = ContactParser()
        self._summary_parser = SummaryParser()
        self._experience_parser = ExperienceParser()
        self._education_parser = EducationParser()
        self._skills_parser = SkillsParser()
        self._certifications_parser = CertificationsParser()
        self._languages_parser = LanguagesParser()
        self._projects_parser = ProjectsParser()
        self._generic_list_parser = GenericListParser()
        self._fallback_manager = FallbackManager()
        self._quality_checker = QualityChecker()

    def parse(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
    ) -> tuple[ResumeContent, QualityReport]:
        content = ResumeContent.build_processing(
            filename=filename,
            mime_type=mime_type,
            parser_version=self._parser_version,
        )

        try:
            extracted = self._extract(file_bytes=file_bytes, filename=filename)
            content.meta.extraction_method = extracted.extraction_method
            content.meta.warnings.extend(extracted.warnings)

            cleaned_blocks = preprocess_blocks(extracted.blocks)
            layout_result = detect_layout_and_reorder(cleaned_blocks)
            content.meta.layout_detected = layout_result.layout_detected

            matches = detect_section_headers(layout_result.blocks)
            sectioned = build_section_map(layout_result.blocks, matches)

            contact_blocks = list(sectioned.header_blocks)
            contact_blocks.extend(sectioned.sections.get("contact", []))
            content.contact = self._contact_parser.parse(contact_blocks)
            if sectioned.sections.get("summary"):
                content.summary = self._summary_parser.parse(sectioned.sections["summary"])
            if sectioned.sections.get("experience"):
                content.experience = self._experience_parser.parse(sectioned.sections["experience"])
            if sectioned.sections.get("education"):
                content.education = self._education_parser.parse(sectioned.sections["education"])
            if sectioned.sections.get("skills"):
                content.skills = self._skills_parser.parse(sectioned.sections["skills"])
            if sectioned.sections.get("certifications"):
                content.certifications = self._certifications_parser.parse(sectioned.sections["certifications"])
            if sectioned.sections.get("languages"):
                content.languages = self._languages_parser.parse(sectioned.sections["languages"])
            if sectioned.sections.get("projects"):
                content.projects = self._projects_parser.parse(sectioned.sections["projects"])

            content = self._fallback_manager.apply(content, layout_result.blocks)
            content.unassigned_blocks = self._collect_unassigned_blocks(
                content=content,
                blocks=layout_result.blocks,
                sectioned=sectioned,
            )

            quality_report = self._quality_checker.evaluate(content, layout_result.blocks)
            content.meta.partial_parse = quality_report.partial_parse
            content.meta.warnings.extend(quality_report.warnings)
            content.meta.warnings = list(dict.fromkeys(content.meta.warnings))
            content.meta.ocr_used = False
            content.meta.parse_status = "completed"
            content.meta.parse_error = None

            if extracted.ocr_candidate:
                content.meta.warnings.append("OCR fallback is not enabled in MVP mode.")
                content.meta.warnings = list(dict.fromkeys(content.meta.warnings))

            return content, quality_report
        except Exception as exc:
            content.meta.parse_status = "failed"
            content.meta.parse_error = str(exc)
            content.meta.partial_parse = True
            content.meta.warnings = list(dict.fromkeys(content.meta.warnings + ["Resume parsing failed."]))
            return content, QualityReport(
                warnings=content.meta.warnings,
                partial_parse=True,
                major_sections_found=[],
            )

    def _extract(self, *, file_bytes: bytes, filename: str):
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return self._pdf_extractor.extract(file_bytes)
        if lower_name.endswith(".docx"):
            return self._docx_extractor.extract(file_bytes)
        raise ValueError("Unsupported file type.")

    def _collect_unassigned_blocks(
        self,
        *,
        content: ResumeContent,
        blocks: list[TextBlock],
        sectioned: SectionedDocument,
    ) -> list[str]:
        if not sectioned.sections:
            return list(dict.fromkeys(block.text for block in sectioned.unassigned_blocks))
        return list(dict.fromkeys(block.text for block in sectioned.unassigned_blocks))
