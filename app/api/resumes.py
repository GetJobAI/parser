from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.config import get_settings
from app.db.repository import ResumeRepository, get_resume_repository
from app.pipeline.resume_pipeline import ResumePipeline
from app.schemas.content import ResumeContent
from app.schemas.response import ParseResumeResponse

router = APIRouter(tags=["resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_resume_pipeline(request: Request) -> ResumePipeline:
    return request.app.state.resume_pipeline


@router.post("/resumes/parse", response_model=ParseResumeResponse, status_code=status.HTTP_201_CREATED)
async def parse_resume(
    request: Request,
    file: UploadFile = File(...),
    repository: ResumeRepository = Depends(get_resume_repository),
    pipeline: ResumePipeline = Depends(get_resume_pipeline),
) -> ParseResumeResponse:
    settings = get_settings()
    header_name = settings.user_id_header
    user_id = request.headers.get(header_name)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing trusted gateway header: {header_name}",
        )

    filename = file.filename or "resume"
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF and DOCX are allowed.",
        )
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES and file.content_type != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported MIME type. Only PDF and DOCX are allowed.",
        )

    processing_content = ResumeContent.build_processing(
        filename=filename,
        mime_type=file.content_type or _mime_from_extension(extension),
        parser_version=settings.parser_version,
    )
    resume_id = await repository.create_resume(user_id=user_id, content=processing_content)

    file_bytes = await file.read()
    if not file_bytes:
        processing_content.meta.parse_status = "failed"
        processing_content.meta.parse_error = "Uploaded file is empty."
        processing_content.meta.partial_parse = True
        processing_content.meta.warnings.append("Uploaded file is empty.")
        await repository.update_content(resume_id=resume_id, content=processing_content)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    content, quality_report = pipeline.parse(
        file_bytes=file_bytes,
        filename=filename,
        mime_type=processing_content.meta.mime_type or "application/octet-stream",
    )
    await repository.update_content(resume_id=resume_id, content=content)

    return ParseResumeResponse(
        resume_id=str(resume_id),
        partial_parse=content.meta.partial_parse,
        warnings=content.meta.warnings,
        major_sections_found=quality_report.major_sections_found,
    )


def _mime_from_extension(extension: str) -> str:
    if extension == ".pdf":
        return "application/pdf"
    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
