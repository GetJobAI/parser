from __future__ import annotations

import json
from uuid import UUID

import asyncpg
from fastapi import Request

from app.schemas.content import ResumeContent


class ResumeRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_resume(self, *, user_id: str, content: ResumeContent) -> UUID:
        query = """
            INSERT INTO public.resumes (user_id, content)
            VALUES ($1, $2::jsonb)
            RETURNING id
        """
        payload = json.dumps(content.model_dump(mode="json"))
        async with self._pool.acquire() as connection:
            resume_id = await connection.fetchval(query, user_id, payload)
        return resume_id

    async def update_content(self, *, resume_id: UUID, content: ResumeContent) -> None:
        query = """
            UPDATE public.resumes
            SET content = $2::jsonb,
                updated_at = now()
            WHERE id = $1
        """
        payload = json.dumps(content.model_dump(mode="json"))
        async with self._pool.acquire() as connection:
            await connection.execute(query, resume_id, payload)


def get_resume_repository(request: Request) -> ResumeRepository:
    return request.app.state.resume_repository
