# Resume Parser Service Integration Notes

## Existing file upload endpoint

The service already exposes the file upload endpoint:

- `POST /resumes/parse`

It accepts:

- `multipart/form-data`
- file field: `file`
- trusted user header: `X-User-Id` by default

## Parsing flags returned by the API

The parse response now exposes these parsing flags:

- `parse_status`
- `partial_parse`
- `fallback_used`
- `ocr_used`
- `extraction_method`
- `layout_detected`
- `has_complex_layout`
- `has_graphics`
- `has_headers_footers`
- `has_non_standard_fonts`
- `event_published`

These are returned together with:

- `resume_id`
- `warnings`
- `major_sections_found`

## Recommended RabbitMQ names

Recommended completion event name:

- `resume.parsing.completed`

Recommended exchange:

- `resume.events`

Recommended routing key:

- `resume.parsing.completed`

Recommended queue name for downstream consumers:

- `resume.parsing.completed.queue`

## Published event payload

After successful parsing and database update, the service publishes the following JSON payload:

```json
{
  "resume_id": "uuid",
  "user_id": "user-id"
}
```

The event type is identified by the RabbitMQ routing key and event name configuration.
