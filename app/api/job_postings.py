from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.job.pipeline import JobPostingPipeline
from app.schemas.job_posting import ParseJobPostingRequest, ParseJobPostingResponse

router = APIRouter(tags=["job-postings"])


def get_job_posting_pipeline(request: Request) -> JobPostingPipeline:
    return request.app.state.job_posting_pipeline


@router.post("/job-postings/parse", response_model=ParseJobPostingResponse, status_code=status.HTTP_200_OK)
async def parse_job_posting(
    payload: ParseJobPostingRequest,
    pipeline: JobPostingPipeline = Depends(get_job_posting_pipeline),
) -> ParseJobPostingResponse:
    content, quality_report = pipeline.parse(
        html=payload.html,
        text=payload.text,
        source_url=payload.source_url,
    )
    return ParseJobPostingResponse(
        parse_status=content.meta.parse_status,
        partial_parse=content.meta.partial_parse,
        extraction_method=content.meta.extraction_method,
        structured_data_used=content.meta.structured_data_used,
        warnings=content.meta.warnings,
        major_sections_found=quality_report.major_sections_found,
        content=content,
    )
