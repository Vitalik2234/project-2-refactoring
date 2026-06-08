import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from src.models import Ticket, TicketStatus, TicketPriority
from src.storage.interfaces import ITicketRepository, IServiceTypeRepository
from src.utils.strategies import IQueueStrategy, FifoStrategy
from src.utils.observers import IQueueObserver


class QueueService:
    """Core service managing queue logic. Service-based architecture."""

    def __init__(
        self,
        ticket_repo: ITicketRepository,
        service_type_repo: IServiceTypeRepository,
        strategy: IQueueStrategy = None,
    ):
        self._ticket_repo = ticket_repo
        self._service_type_repo = service_type_repo
        self._strategy: IQueueStrategy = strategy or FifoStrategy()
        self._observers: List[IQueueObserver] = []
        self._counters: dict = {}  # service_type -> last number

    def add_observer(self, observer: IQueueObserver) -> None:
        self._observers.append(observer)

    def set_strategy(self, strategy: IQueueStrategy) -> None:
        self._strategy = strategy

    def get_strategy_name(self) -> str:
        return self._strategy.get_name()

    def _next_number(self, service_type: str) -> int:
        self._counters[service_type] = self._counters.get(service_type, 0) + 1
        return self._counters[service_type]

    def _notify_created(self, ticket: Ticket) -> None:
        for obs in self._observers:
            obs.on_ticket_created(ticket)

    def _notify_called(self, ticket: Ticket, window_name: str) -> None:
        for obs in self._observers:
            obs.on_ticket_called(ticket, window_name)

    def _notify_completed(self, ticket: Ticket) -> None:
        for obs in self._observers:
            obs.on_ticket_completed(ticket)

    def _notify_cancelled(self, ticket: Ticket) -> None:
        for obs in self._observers:
            obs.on_ticket_cancelled(ticket)

    def _notify_missed(self, ticket: Ticket) -> None:
        for obs in self._observers:
            obs.on_ticket_missed(ticket)

    def issue_ticket(
        self,
        service_type: str,
        customer_name: Optional[str] = None,
        notification_phone: Optional[str] = None,
        priority: TicketPriority = TicketPriority.NORMAL,
    ) -> Ticket:
        service = self._service_type_repo.find_by_id(service_type)
        if not service or not service.is_active:
            raise ValueError(f"Service type '{service_type}' not found or inactive.")

        waiting = self._ticket_repo.count_waiting(service_type)
        avg_duration = service.avg_duration_minutes
        estimated_wait = int(waiting * avg_duration)
        number = self._next_number(service_type)

        ticket = Ticket(
            ticket_id=str(uuid.uuid4()),
            number=number,
            service_type=service_type,
            status=TicketStatus.WAITING,
            priority=priority,
            created_at=datetime.now(),
            customer_name=customer_name,
            notification_phone=notification_phone,
            estimated_wait_minutes=estimated_wait,
            position_in_queue=waiting + 1,
        )
        self._ticket_repo.save(ticket)
        self._notify_created(ticket)
        return ticket

    def get_queue(self, service_type: Optional[str] = None) -> List[Ticket]:
        waiting = self._ticket_repo.find_by_status(TicketStatus.WAITING)
        if service_type:
            waiting = [t for t in waiting if t.service_type == service_type]
        return self._strategy.sort(waiting)

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        return self._ticket_repo.find_by_id(ticket_id)

    def call_next(self, service_type: str, window_id: str, window_name: str) -> Optional[Ticket]:
        queue = self.get_queue(service_type)
        if not queue:
            return None
        ticket = queue[0]
        ticket.status = TicketStatus.CALLED
        ticket.called_at = datetime.now()
        ticket.window_id = window_id
        self._ticket_repo.save(ticket)
        self._notify_called(ticket, window_name)
        return ticket

    def call_specific(self, ticket_id: str, window_id: str, window_name: str) -> Ticket:
        ticket = self._ticket_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found.")
        if ticket.status != TicketStatus.WAITING:
            raise ValueError(f"Ticket {ticket_id} is not in waiting status.")
        ticket.status = TicketStatus.CALLED
        ticket.called_at = datetime.now()
        ticket.window_id = window_id
        self._ticket_repo.save(ticket)
        self._notify_called(ticket, window_name)
        return ticket

    def start_serving(self, ticket_id: str) -> Ticket:
        ticket = self._ticket_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found.")
        if ticket.status != TicketStatus.CALLED:
            raise ValueError(f"Ticket {ticket_id} is not in called status.")
        ticket.status = TicketStatus.SERVING
        self._ticket_repo.save(ticket)
        return ticket

    def complete_ticket(self, ticket_id: str) -> Ticket:
        ticket = self._ticket_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found.")
        if ticket.status not in (TicketStatus.CALLED, TicketStatus.SERVING):
            raise ValueError(f"Ticket {ticket_id} cannot be completed from status {ticket.status}.")
        ticket.status = TicketStatus.COMPLETED
        ticket.completed_at = datetime.now()
        self._ticket_repo.save(ticket)
        self._notify_completed(ticket)
        return ticket

    def cancel_ticket(self, ticket_id: str) -> Ticket:
        ticket = self._ticket_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found.")
        if ticket.status in (TicketStatus.COMPLETED, TicketStatus.CANCELLED):
            raise ValueError(f"Ticket {ticket_id} is already finalized.")
        ticket.status = TicketStatus.CANCELLED
        self._ticket_repo.save(ticket)
        self._notify_cancelled(ticket)
        return ticket

    def mark_missed(self, ticket_id: str) -> Ticket:
        ticket = self._ticket_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found.")
        if ticket.status != TicketStatus.CALLED:
            raise ValueError(f"Ticket {ticket_id} is not in called status.")
        ticket.status = TicketStatus.MISSED
        self._ticket_repo.save(ticket)
        self._notify_missed(ticket)
        return ticket

    def get_queue_stats(self) -> dict:
        all_tickets = self._ticket_repo.find_all()
        return {
            "waiting": sum(1 for t in all_tickets if t.status == TicketStatus.WAITING),
            "called": sum(1 for t in all_tickets if t.status == TicketStatus.CALLED),
            "serving": sum(1 for t in all_tickets if t.status == TicketStatus.SERVING),
            "completed": sum(1 for t in all_tickets if t.status == TicketStatus.COMPLETED),
            "cancelled": sum(1 for t in all_tickets if t.status == TicketStatus.CANCELLED),
            "missed": sum(1 for t in all_tickets if t.status == TicketStatus.MISSED),
            "total": len(all_tickets),
        }

    def get_position(self, ticket_id: str) -> Tuple[int, int]:
        """Returns (position, estimated_wait_minutes)."""
        ticket = self._ticket_repo.find_by_id(ticket_id)
        if not ticket or ticket.status != TicketStatus.WAITING:
            return 0, 0
        queue = self.get_queue(ticket.service_type)
        for i, t in enumerate(queue):
            if t.ticket_id == ticket_id:
                service = self._service_type_repo.find_by_id(ticket.service_type)
                avg = service.avg_duration_minutes if service else 5.0
                return i + 1, int(i * avg)
        return 0, 0
