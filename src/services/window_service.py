import uuid
from typing import List, Optional

from src.models import ServiceWindow, WindowStatus
from src.storage.interfaces import IWindowRepository


class WindowService:
    def __init__(self, window_repo: IWindowRepository):
        self._repo = window_repo

    def create_window(self, name: str, service_types: List[str], operator_name: Optional[str] = None) -> ServiceWindow:
        if not name.strip():
            raise ValueError("Window name cannot be empty.")
        if not service_types:
            raise ValueError("Window must serve at least one service type.")
        window = ServiceWindow(
            window_id=str(uuid.uuid4()),
            name=name,
            service_types=service_types,
            status=WindowStatus.CLOSED,
            operator_name=operator_name,
        )
        return self._repo.save(window)

    def open_window(self, window_id: str) -> ServiceWindow:
        window = self._get_or_raise(window_id)
        window.status = WindowStatus.OPEN
        return self._repo.save(window)

    def close_window(self, window_id: str) -> ServiceWindow:
        window = self._get_or_raise(window_id)
        window.status = WindowStatus.CLOSED
        window.current_ticket_id = None
        return self._repo.save(window)

    def set_break(self, window_id: str) -> ServiceWindow:
        window = self._get_or_raise(window_id)
        window.status = WindowStatus.BREAK
        return self._repo.save(window)

    def assign_ticket(self, window_id: str, ticket_id: str) -> ServiceWindow:
        window = self._get_or_raise(window_id)
        if window.status != WindowStatus.OPEN:
            raise ValueError(f"Window {window_id} is not open.")
        window.current_ticket_id = ticket_id
        window.status = WindowStatus.BUSY
        return self._repo.save(window)

    def free_window(self, window_id: str) -> ServiceWindow:
        window = self._get_or_raise(window_id)
        window.current_ticket_id = None
        window.status = WindowStatus.OPEN
        window.tickets_served_today += 1
        return self._repo.save(window)

    def get_all_windows(self) -> List[ServiceWindow]:
        return self._repo.find_all()

    def get_window(self, window_id: str) -> Optional[ServiceWindow]:
        return self._repo.find_by_id(window_id)

    def get_available_windows(self, service_type: str) -> List[ServiceWindow]:
        return self._repo.find_available_for_service(service_type)

    def delete_window(self, window_id: str) -> bool:
        self._get_or_raise(window_id)
        return self._repo.delete(window_id)

    def _get_or_raise(self, window_id: str) -> ServiceWindow:
        window = self._repo.find_by_id(window_id)
        if not window:
            raise ValueError(f"Window '{window_id}' not found.")
        return window
