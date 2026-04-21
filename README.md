# Resume Parser Service

MVP resume parsing microservice for a broader microservice platform.

## Assumptions

- The API gateway authenticates requests and forwards a trusted user id via `X-User-Id`.
- This service creates rows in the existing `public.resumes` table and stores all parse state inside `content`.
- Uploaded files are processed immediately and are not stored permanently.

## Run

```bash
uvicorn app.main:app --reload
```

Required environment variables:

- `DATABASE_URL`
- `USER_ID_HEADER` (optional, defaults to `X-User-Id`)
- `PARSER_VERSION` (optional, defaults to `v1`)

## Extension points

- OCR fallback is intentionally left as a hook when a PDF has little or no text layer.
- AI-assisted parsing is intentionally left as an optional future hook for only weak/ambiguous blocks.
