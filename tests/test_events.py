"""Tests for events module."""

from droid_agent_sdk.events import AgentMessage, Event, EventType


def test_event_from_notification():
    notification = {
        "type": "assistant_text_delta",
        "messageId": "msg-1",
        "textDelta": "Hello",
    }
    
    event = Event.from_notification(notification)
    assert event.type == EventType.TEXT_DELTA
    assert event.message_id == "msg-1"
    assert event.text == "Hello"


def test_event_unknown_type():
    notification = {"type": "some_unknown_type"}
    event = Event.from_notification(notification)
    assert event.type == EventType.UNKNOWN


def test_agent_message_format():
    msg = AgentMessage(
        from_agent="opus",
        to_agent="orchestrator",
        content="Review complete",
    )
    
    formatted = msg.format()
    assert '<MESSAGE from="opus" to="orchestrator">' in formatted
    assert "Review complete" in formatted
    assert "</MESSAGE>" in formatted


def test_agent_message_parse():
    text = '<MESSAGE from="opus" to="orchestrator">\nReview complete, no issues found.\n</MESSAGE>'
    msg = AgentMessage.parse(text)
    
    assert msg is not None
    assert msg.from_agent == "opus"
    assert msg.to_agent == "orchestrator"
    assert msg.content == "Review complete, no issues found."


def test_agent_message_to_dict():
    msg = AgentMessage(
        from_agent="opus",
        to_agent="orchestrator",
        content="Done",
        timestamp="2025-01-18T12:00:00Z",
    )
    
    d = msg.to_dict()
    assert d["from"] == "opus"
    assert d["to"] == "orchestrator"
    assert d["content"] == "Done"
    assert d["timestamp"] == "2025-01-18T12:00:00Z"
