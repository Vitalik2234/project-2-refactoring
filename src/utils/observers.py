from abc import ABC, abstractmethod
from typing import List
from src.models import Ticket, Notification, NotificationType
import uuid
from datetime import datetime


class IQueueObserver(ABC):
    """Observer pattern for queue events."""

    @abstractmethod
    def on_ticket_created(self, ticket: Ticket) -> None: ...

    @abstractmethod
    def on_ticket_called(self, ticket: Ticket, window_name: str) -> None: ...

    @abstractmethod
    def on_ticket_completed(self, ticket: Ticket) -> None: ...

    @abstractmethod
    def on_ticket_cancelled(self, ticket: Ticket) -> None: ...

    @abstractmethod
    def on_ticket_missed(self, ticket: Ticket) -> None: ...


class NotificationObserver(IQueueObserver):
    """Creates notification records on queue events."""

    def __init__(self, notification_repo):
        self._repo = notification_repo

    def _create(self, ticket: Ticket, ntype: NotificationType, message: str, recipient: str = None) -> Notification:
        n = Notification(
            notification_id=str(uuid.uuid4()),
            ticket_id=ticket.ticket_id,
            notification_type=ntype,
            message=message,
            created_at=datetime.now(),
            sent=False,
            recipient=recipient or ticket.notification_phone,
        )
        self._repo.save(n)
        return n

    def on_ticket_created(self, ticket: Ticket) -> None:
        self._create(
            ticket, NotificationType.TICKET_CREATED,
            f"Ваш талон #{ticket.number} для послуги '{ticket.service_type}' створено. "
            f"Очікуйте, ваша позиція: {ticket.position_in_queue}.",
        )

    def on_ticket_called(self, ticket: Ticket, window_name: str) -> None:
        self._create(
            ticket, NotificationType.CALLED_TO_WINDOW,
            f"Талон #{ticket.number} — запрошуємо до {window_name}. Підійдіть, будь ласка.",
        )

    def on_ticket_completed(self, ticket: Ticket) -> None:
        self._create(
            ticket, NotificationType.TICKET_COMPLETED,
            f"Обслуговування за талоном #{ticket.number} завершено. Дякуємо!",
        )

    def on_ticket_cancelled(self, ticket: Ticket) -> None:
        self._create(
            ticket, NotificationType.TICKET_CANCELLED,
            f"Талон #{ticket.number} скасовано.",
        )

    def on_ticket_missed(self, ticket: Ticket) -> None:
        self._create(
            ticket, NotificationType.TICKET_MISSED,
            f"Талон #{ticket.number} анульовано — вас не було на місці.",
        )


class LoggingObserver(IQueueObserver):
    """Logs all queue events (for debugging / audit)."""

    def __init__(self):
        self._events: List[dict] = []

    def on_ticket_created(self, ticket: Ticket) -> None:
        self._events.append({"event": "created", "ticket_id": ticket.ticket_id, "time": datetime.now().isoformat()})

    def on_ticket_called(self, ticket: Ticket, window_name: str) -> None:
        self._events.append({"event": "called", "ticket_id": ticket.ticket_id, "window": window_name, "time": datetime.now().isoformat()})

    def on_ticket_completed(self, ticket: Ticket) -> None:
        self._events.append({"event": "completed", "ticket_id": ticket.ticket_id, "time": datetime.now().isoformat()})

    def on_ticket_cancelled(self, ticket: Ticket) -> None:
        self._events.append({"event": "cancelled", "ticket_id": ticket.ticket_id, "time": datetime.now().isoformat()})

    def on_ticket_missed(self, ticket: Ticket) -> None:
        self._events.append({"event": "missed", "ticket_id": ticket.ticket_id, "time": datetime.now().isoformat()})

    def get_events(self) -> List[dict]:
        return list(self._events)
