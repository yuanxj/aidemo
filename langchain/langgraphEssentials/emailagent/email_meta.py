from typing import Literal, TypedDict
from enum import Enum


class EmailClassification(TypedDict):
    """Email classification result with intent, urgency, topic, and summary."""
    intent: Literal['support', 'sales', 'marketing', 'other']
    urgency: Literal['low', 'medium', 'high']
    topic: str
    summary: str


class EmailAgentState(TypedDict):
    """State class for Email Agent with all required attributes."""
    #raw data
    email_content: str
    sender_email: str
    email_id: str

    #classification result
    classification: EmailClassification | None

    #bug tracking
    ticket_id: str
    search_results: list[str] | None
    draft_response: str | None

