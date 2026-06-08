from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class WindowStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    BREAK = "break"
    BUSY = "busy"


@dataclass
class ServiceWindow:
    window_id: str
    name: str
    service_types: List[str] = field(default_factory=list)
    status: WindowStatus = WindowStatus.CLOSED
    operator_name: Optional[str] = None
    current_ticket_id: Optional[str] = None
    tickets_served_today: int = 0
    average_service_minutes: float = 5.0

    def can_serve(self, service_type: str) -> bool:
        return service_type in self.service_types and self.status == WindowStatus.OPEN

    def to_dict(self) -> dict:
        return {
            "window_id": self.window_id,
            "name": self.name,
            "service_types": self.service_types,
            "status": self.status.value,
            "operator_name": self.operator_name,
            "current_ticket_id": self.current_ticket_id,
            "tickets_served_today": self.tickets_served_today,
            "average_service_minutes": self.average_service_minutes,
        }
