from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


@dataclass
class ServiceType:
    service_id: str
    name: str
    description: str = ""
    avg_duration_minutes: float = 5.0
    prefix: str = "A"
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "description": self.description,
            "avg_duration_minutes": self.avg_duration_minutes,
            "prefix": self.prefix,
            "is_active": self.is_active,
        }


class NotificationType(Enum):
    TICKET_CREATED = "ticket_created"
    CALLED_TO_WINDOW = "called_to_window"
    TURN_SOON = "turn_soon"
    TICKET_CANCELLED = "ticket_cancelled"
    TICKET_MISSED = "ticket_missed"
    TICKET_COMPLETED = "ticket_completed"


@dataclass
class Notification:
    notification_id: str
    ticket_id: str
    notification_type: NotificationType
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    sent: bool = False
    recipient: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "notification_id": self.notification_id,
            "ticket_id": self.ticket_id,
            "type": self.notification_type.value,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "sent": self.sent,
            "recipient": self.recipient,
        }
