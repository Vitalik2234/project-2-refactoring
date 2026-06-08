from abc import ABC, abstractmethod
from typing import List
from src.models import Ticket, TicketPriority


class IQueueStrategy(ABC):
    """Strategy pattern for queue ordering algorithms."""

    @abstractmethod
    def sort(self, tickets: List[Ticket]) -> List[Ticket]:
        ...

    @abstractmethod
    def get_name(self) -> str:
        ...


class FifoStrategy(IQueueStrategy):
    """First In First Out - standard queue."""

    def sort(self, tickets: List[Ticket]) -> List[Ticket]:
        return sorted(tickets, key=lambda t: t.created_at)

    def get_name(self) -> str:
        return "FIFO"


class PriorityStrategy(IQueueStrategy):
    """Priority-based queue: VIP > PRIORITY > NORMAL, then by time."""

    def sort(self, tickets: List[Ticket]) -> List[Ticket]:
        return sorted(
            tickets,
            key=lambda t: (-t.priority.value, t.created_at)
        )

    def get_name(self) -> str:
        return "PRIORITY"


class ShortestJobFirstStrategy(IQueueStrategy):
    """Shortest estimated service time first."""

    def sort(self, tickets: List[Ticket]) -> List[Ticket]:
        return sorted(tickets, key=lambda t: t.estimated_wait_minutes)

    def get_name(self) -> str:
        return "SJF"
