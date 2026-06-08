import pytest
from src.storage.in_memory import (
    InMemoryTicketRepository, InMemoryWindowRepository,
    InMemoryServiceTypeRepository, InMemoryNotificationRepository,
)
from src.services import QueueService, WindowService, ServiceTypeService, NotificationService
from src.utils.observers import NotificationObserver, LoggingObserver
from src.utils.strategies import FifoStrategy, PriorityStrategy, ShortestJobFirstStrategy
from src.models import TicketPriority


@pytest.fixture
def ticket_repo():
    return InMemoryTicketRepository()

@pytest.fixture
def window_repo():
    return InMemoryWindowRepository()

@pytest.fixture
def service_repo():
    return InMemoryServiceTypeRepository()

@pytest.fixture
def notif_repo():
    return InMemoryNotificationRepository()

@pytest.fixture
def service_type_service(service_repo):
    return ServiceTypeService(service_repo)

@pytest.fixture
def window_service(window_repo):
    return WindowService(window_repo)

@pytest.fixture
def notification_service(notif_repo):
    return NotificationService(notif_repo)

@pytest.fixture
def queue_service(ticket_repo, service_repo):
    return QueueService(ticket_repo, service_repo, FifoStrategy())

@pytest.fixture
def sample_service(service_type_service):
    return service_type_service.create_service("Консультація", "Опис", 5.0, "K")

@pytest.fixture
def sample_window(window_service, sample_service):
    w = window_service.create_window("Вікно 1", [sample_service.service_id], "Іваненко")
    window_service.open_window(w.window_id)
    return w

@pytest.fixture
def full_setup(ticket_repo, service_repo, window_repo, notif_repo):
    """Full setup with all services wired together."""
    svc_service = ServiceTypeService(service_repo)
    win_service = WindowService(window_repo)
    notif_service = NotificationService(notif_repo)
    q_service = QueueService(ticket_repo, service_repo, FifoStrategy())
    notif_obs = NotificationObserver(notif_repo)
    log_obs = LoggingObserver()
    q_service.add_observer(notif_obs)
    q_service.add_observer(log_obs)
    s = svc_service.create_service("Тест", "Тестова послуга", 5.0, "T")
    w = win_service.create_window("Вікно 1", [s.service_id], "Оператор")
    win_service.open_window(w.window_id)
    return {
        "queue": q_service,
        "windows": win_service,
        "services": svc_service,
        "notifications": notif_service,
        "service": s,
        "window": w,
        "log_obs": log_obs,
    }
