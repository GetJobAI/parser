from app.events.publisher import ResumeParsedEventPublisher


def test_resume_parsed_event_payload_contains_resume_and_user_ids() -> None:
    publisher = ResumeParsedEventPublisher(
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        exchange_name="resume.events",
        routing_key="resume.parsing.completed",
        event_name="resume.parsing.completed",
        queue_name="resume.parsing.completed.queue",
    )

    payload = publisher.build_payload(resume_id="resume-123", user_id="user-456")

    assert payload == {
        "resume_id": "resume-123",
        "user_id": "user-456",
    }
