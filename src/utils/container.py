from src.storage.in_memory import (
    InMemoryTicketRepository, InMemoryWindowRepository,
    InMemoryServiceTypeRepository, InMemoryNotificationRepository,
)
from src.services.queue_service import QueueService
from src.services.window_service import WindowService
from src.services.service_type_service import ServiceTypeService, NotificationService
from src.utils.observers import NotificationObserver, LoggingObserver
from src.utils.strategies import FifoStrategy


class Container:
    """Simple DI container — single instance per app."""

    def __init__(self):
        # Repositories
        self.ticket_repo = InMemoryTicketRepository()
        self.window_repo = InMemoryWindowRepository()
        self.service_type_repo = InMemoryServiceTypeRepository()
        self.notification_repo = InMemoryNotificationRepository()

        # Services
        self.service_type_service = ServiceTypeService(self.service_type_repo)
        self.window_service = WindowService(self.window_repo)
        self.notification_service = NotificationService(self.notification_repo)
        self.queue_service = QueueService(
            self.ticket_repo,
            self.service_type_repo,
            FifoStrategy(),
        )

        # Observers (Observer pattern)
        self.logging_observer = LoggingObserver()
        self.notification_observer = NotificationObserver(self.notification_repo)
        self.queue_service.add_observer(self.notification_observer)
        self.queue_service.add_observer(self.logging_observer)

    def seed_demo_data(self):
        """Seed with sample data for demo purposes."""
        # Services
        s1 = self.service_type_service.create_service("Консультація", "Загальна консультація", 10.0, "K")
        s2 = self.service_type_service.create_service("Оплата", "Оплата послуг та рахунків", 5.0, "O")
        s3 = self.service_type_service.create_service("Довідка", "Видача довідок та документів", 7.0, "D")

        # Windows
        w1 = self.window_service.create_window("Вікно 1", [s1.service_id, s2.service_id], "Іванenko О.")
        w2 = self.window_service.create_window("Вікно 2", [s2.service_id, s3.service_id], "Петренко М.")
        w3 = self.window_service.create_window("Вікно 3", [s1.service_id, s3.service_id], "Коваленко В.")
        self.window_service.open_window(w1.window_id)
        self.window_service.open_window(w2.window_id)

        return {"services": [s1, s2, s3], "windows": [w1, w2, w3]}


# Singleton container
_container: Container = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
        _container.seed_demo_data()
    return _container


def reset_container():
    """For testing purposes."""
    global _container
    _container = None
