from typing import List, Optional, Dict
from src.models import Ticket, TicketStatus, ServiceWindow, WindowStatus, ServiceType, Notification
from src.storage.interfaces import (
    ITicketRepository, IWindowRepository,
    IServiceTypeRepository, INotificationRepository
)


class InMemoryTicketRepository(ITicketRepository):
    def __init__(self):
        self._store: Dict[str, Ticket] = {}

    def save(self, ticket: Ticket) -> Ticket:
        self._store[ticket.ticket_id] = ticket
        return ticket

    def find_by_id(self, ticket_id: str) -> Optional[Ticket]:
        return self._store.get(ticket_id)

    def find_all(self) -> List[Ticket]:
        return list(self._store.values())

    def find_by_status(self, status: TicketStatus) -> List[Ticket]:
        return [t for t in self._store.values() if t.status == status]

    def find_by_service_type(self, service_type: str) -> List[Ticket]:
        return [t for t in self._store.values() if t.service_type == service_type]

    def delete(self, ticket_id: str) -> bool:
        if ticket_id in self._store:
            del self._store[ticket_id]
            return True
        return False

    def count_waiting(self, service_type: str) -> int:
        return sum(
            1 for t in self._store.values()
            if t.service_type == service_type and t.status == TicketStatus.WAITING
        )

    def clear(self):
        self._store.clear()


class InMemoryWindowRepository(IWindowRepository):
    def __init__(self):
        self._store: Dict[str, ServiceWindow] = {}

    def save(self, window: ServiceWindow) -> ServiceWindow:
        self._store[window.window_id] = window
        return window

    def find_by_id(self, window_id: str) -> Optional[ServiceWindow]:
        return self._store.get(window_id)

    def find_all(self) -> List[ServiceWindow]:
        return list(self._store.values())

    def find_available_for_service(self, service_type: str) -> List[ServiceWindow]:
        return [
            w for w in self._store.values()
            if w.can_serve(service_type) and w.current_ticket_id is None
        ]

    def delete(self, window_id: str) -> bool:
        if window_id in self._store:
            del self._store[window_id]
            return True
        return False

    def clear(self):
        self._store.clear()


class InMemoryServiceTypeRepository(IServiceTypeRepository):
    def __init__(self):
        self._store: Dict[str, ServiceType] = {}

    def save(self, service_type: ServiceType) -> ServiceType:
        self._store[service_type.service_id] = service_type
        return service_type

    def find_by_id(self, service_id: str) -> Optional[ServiceType]:
        return self._store.get(service_id)

    def find_all(self) -> List[ServiceType]:
        return list(self._store.values())

    def find_active(self) -> List[ServiceType]:
        return [s for s in self._store.values() if s.is_active]

    def delete(self, service_id: str) -> bool:
        if service_id in self._store:
            del self._store[service_id]
            return True
        return False

    def clear(self):
        self._store.clear()


class InMemoryNotificationRepository(INotificationRepository):
    def __init__(self):
        self._store: Dict[str, Notification] = {}

    def save(self, notification: Notification) -> Notification:
        self._store[notification.notification_id] = notification
        return notification

    def find_by_ticket_id(self, ticket_id: str) -> List[Notification]:
        return [n for n in self._store.values() if n.ticket_id == ticket_id]

    def find_unsent(self) -> List[Notification]:
        return [n for n in self._store.values() if not n.sent]

    def find_all(self) -> List[Notification]:
        return list(self._store.values())

    def mark_sent(self, notification_id: str) -> bool:
        if notification_id in self._store:
            self._store[notification_id].sent = True
            return True
        return False

    def clear(self):
        self._store.clear()
