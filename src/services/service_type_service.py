import uuid
from typing import List, Optional

from src.models import ServiceType, Notification
from src.storage.interfaces import IServiceTypeRepository, INotificationRepository


class ServiceTypeService:
    def __init__(self, repo: IServiceTypeRepository):
        self._repo = repo

    def create_service(self, name: str, description: str = "", avg_duration: float = 5.0, prefix: str = "A") -> ServiceType:
        if not name.strip():
            raise ValueError("Service name cannot be empty.")
        if avg_duration <= 0:
            raise ValueError("Average duration must be positive.")
        service = ServiceType(
            service_id=str(uuid.uuid4()),
            name=name,
            description=description,
            avg_duration_minutes=avg_duration,
            prefix=prefix,
            is_active=True,
        )
        return self._repo.save(service)

    def get_all(self) -> List[ServiceType]:
        return self._repo.find_all()

    def get_active(self) -> List[ServiceType]:
        return self._repo.find_active()

    def get_by_id(self, service_id: str) -> Optional[ServiceType]:
        return self._repo.find_by_id(service_id)

    def deactivate(self, service_id: str) -> ServiceType:
        service = self._get_or_raise(service_id)
        service.is_active = False
        return self._repo.save(service)

    def activate(self, service_id: str) -> ServiceType:
        service = self._get_or_raise(service_id)
        service.is_active = True
        return self._repo.save(service)

    def delete(self, service_id: str) -> bool:
        self._get_or_raise(service_id)
        return self._repo.delete(service_id)

    def _get_or_raise(self, service_id: str) -> ServiceType:
        s = self._repo.find_by_id(service_id)
        if not s:
            raise ValueError(f"ServiceType '{service_id}' not found.")
        return s


class NotificationService:
    def __init__(self, repo: INotificationRepository):
        self._repo = repo

    def get_for_ticket(self, ticket_id: str) -> List[Notification]:
        return self._repo.find_by_ticket_id(ticket_id)

    def get_unsent(self) -> List[Notification]:
        return self._repo.find_unsent()

    def mark_sent(self, notification_id: str) -> bool:
        return self._repo.mark_sent(notification_id)

    def get_all(self) -> List[Notification]:
        return self._repo.find_all()

    def process_pending(self) -> int:
        """Simulate sending unsent notifications. Returns count processed."""
        unsent = self._repo.find_unsent()
        count = 0
        for n in unsent:
            # In real system: send SMS/email here
            self._repo.mark_sent(n.notification_id)
            count += 1
        return count
