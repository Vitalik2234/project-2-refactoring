from abc import ABC, abstractmethod
from typing import List, Optional
from src.models import Ticket, ServiceWindow, ServiceType, Notification


class ITicketRepository(ABC):
    @abstractmethod
    def save(self, ticket: Ticket) -> Ticket: ...

    @abstractmethod
    def find_by_id(self, ticket_id: str) -> Optional[Ticket]: ...

    @abstractmethod
    def find_all(self) -> List[Ticket]: ...

    @abstractmethod
    def find_by_status(self, status) -> List[Ticket]: ...

    @abstractmethod
    def find_by_service_type(self, service_type: str) -> List[Ticket]: ...

    @abstractmethod
    def delete(self, ticket_id: str) -> bool: ...

    @abstractmethod
    def count_waiting(self, service_type: str) -> int: ...


class IWindowRepository(ABC):
    @abstractmethod
    def save(self, window: ServiceWindow) -> ServiceWindow: ...

    @abstractmethod
    def find_by_id(self, window_id: str) -> Optional[ServiceWindow]: ...

    @abstractmethod
    def find_all(self) -> List[ServiceWindow]: ...

    @abstractmethod
    def find_available_for_service(self, service_type: str) -> List[ServiceWindow]: ...

    @abstractmethod
    def delete(self, window_id: str) -> bool: ...


class IServiceTypeRepository(ABC):
    @abstractmethod
    def save(self, service_type: ServiceType) -> ServiceType: ...

    @abstractmethod
    def find_by_id(self, service_id: str) -> Optional[ServiceType]: ...

    @abstractmethod
    def find_all(self) -> List[ServiceType]: ...

    @abstractmethod
    def find_active(self) -> List[ServiceType]: ...

    @abstractmethod
    def delete(self, service_id: str) -> bool: ...


class INotificationRepository(ABC):
    @abstractmethod
    def save(self, notification: Notification) -> Notification: ...

    @abstractmethod
    def find_by_ticket_id(self, ticket_id: str) -> List[Notification]: ...

    @abstractmethod
    def find_unsent(self) -> List[Notification]: ...

    @abstractmethod
    def find_all(self) -> List[Notification]: ...

    @abstractmethod
    def mark_sent(self, notification_id: str) -> bool: ...
