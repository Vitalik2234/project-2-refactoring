from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TicketStatus(Enum):
    WAITING = "waiting"
    CALLED = "called"
    SERVING = "serving"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    MISSED = "missed"


class TicketPriority(Enum):
    NORMAL = 1
    PRIORITY = 2  # elderly, disabled
    VIP = 3


@dataclass
class Ticket:
    ticket_id: str
    number: int
    service_type: str
    status: TicketStatus = TicketStatus.WAITING
    priority: TicketPriority = TicketPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    called_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    window_id: Optional[str] = None
    customer_name: Optional[str] = None
    notification_phone: Optional[str] = None
    estimated_wait_minutes: int = 0
    position_in_queue: int = 0

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "number": self.number,
            "service_type": self.service_type,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "called_at": self.called_at.isoformat() if self.called_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "window_id": self.window_id,
            "customer_name": self.customer_name,
            "notification_phone": self.notification_phone,
            "estimated_wait_minutes": self.estimated_wait_minutes,
            "position_in_queue": self.position_in_queue,
        }
