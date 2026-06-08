import pytest
from src.models import Ticket, TicketStatus, TicketPriority, ServiceWindow, WindowStatus, ServiceType, Notification, NotificationType
from src.storage.in_memory import (
    InMemoryTicketRepository, InMemoryWindowRepository,
    InMemoryServiceTypeRepository, InMemoryNotificationRepository,
)


# ─── Ticket Repository ─────────────────────────────────────────────────────────

class TestInMemoryTicketRepository:
    def test_save_and_find_by_id(self, ticket_repo):
        t = Ticket("t1", 1, "svc1")
        ticket_repo.save(t)
        found = ticket_repo.find_by_id("t1")
        assert found is not None
        assert found.ticket_id == "t1"

    def test_find_by_id_not_found(self, ticket_repo):
        assert ticket_repo.find_by_id("nonexistent") is None

    def test_find_all_empty(self, ticket_repo):
        assert ticket_repo.find_all() == []

    def test_find_all_returns_all(self, ticket_repo):
        ticket_repo.save(Ticket("t1", 1, "svc1"))
        ticket_repo.save(Ticket("t2", 2, "svc1"))
        assert len(ticket_repo.find_all()) == 2

    def test_save_overwrites_existing(self, ticket_repo):
        t = Ticket("t1", 1, "svc1")
        ticket_repo.save(t)
        t.status = TicketStatus.COMPLETED
        ticket_repo.save(t)
        assert ticket_repo.find_by_id("t1").status == TicketStatus.COMPLETED

    def test_find_by_status_waiting(self, ticket_repo):
        ticket_repo.save(Ticket("t1", 1, "svc1", status=TicketStatus.WAITING))
        ticket_repo.save(Ticket("t2", 2, "svc1", status=TicketStatus.COMPLETED))
        waiting = ticket_repo.find_by_status(TicketStatus.WAITING)
        assert len(waiting) == 1
        assert waiting[0].ticket_id == "t1"

    def test_find_by_status_empty(self, ticket_repo):
        assert ticket_repo.find_by_status(TicketStatus.CALLED) == []

    def test_find_by_service_type(self, ticket_repo):
        ticket_repo.save(Ticket("t1", 1, "svc1"))
        ticket_repo.save(Ticket("t2", 2, "svc2"))
        result = ticket_repo.find_by_service_type("svc1")
        assert len(result) == 1
        assert result[0].ticket_id == "t1"

    def test_delete_existing(self, ticket_repo):
        ticket_repo.save(Ticket("t1", 1, "svc1"))
        assert ticket_repo.delete("t1") is True
        assert ticket_repo.find_by_id("t1") is None

    def test_delete_nonexistent(self, ticket_repo):
        assert ticket_repo.delete("ghost") is False

    def test_count_waiting(self, ticket_repo):
        ticket_repo.save(Ticket("t1", 1, "svc1", status=TicketStatus.WAITING))
        ticket_repo.save(Ticket("t2", 2, "svc1", status=TicketStatus.WAITING))
        ticket_repo.save(Ticket("t3", 3, "svc1", status=TicketStatus.COMPLETED))
        assert ticket_repo.count_waiting("svc1") == 2

    def test_count_waiting_different_service(self, ticket_repo):
        ticket_repo.save(Ticket("t1", 1, "svc1", status=TicketStatus.WAITING))
        assert ticket_repo.count_waiting("svc2") == 0

    def test_count_waiting_zero(self, ticket_repo):
        assert ticket_repo.count_waiting("svc1") == 0

    def test_clear(self, ticket_repo):
        ticket_repo.save(Ticket("t1", 1, "svc1"))
        ticket_repo.clear()
        assert ticket_repo.find_all() == []

    def test_multiple_statuses(self, ticket_repo):
        for i, status in enumerate(TicketStatus):
            ticket_repo.save(Ticket(f"t{i}", i, "svc1", status=status))
        for status in TicketStatus:
            result = ticket_repo.find_by_status(status)
            assert len(result) == 1


# ─── Window Repository ─────────────────────────────────────────────────────────

class TestInMemoryWindowRepository:
    def test_save_and_find(self, window_repo):
        w = ServiceWindow("w1", "Вікно 1", ["svc1"])
        window_repo.save(w)
        assert window_repo.find_by_id("w1") is not None

    def test_find_not_found(self, window_repo):
        assert window_repo.find_by_id("ghost") is None

    def test_find_all(self, window_repo):
        window_repo.save(ServiceWindow("w1", "В1", ["s1"]))
        window_repo.save(ServiceWindow("w2", "В2", ["s2"]))
        assert len(window_repo.find_all()) == 2

    def test_find_available_for_service(self, window_repo):
        w1 = ServiceWindow("w1", "В1", ["svc1"], status=WindowStatus.OPEN)
        w2 = ServiceWindow("w2", "В2", ["svc2"], status=WindowStatus.OPEN)
        window_repo.save(w1)
        window_repo.save(w2)
        result = window_repo.find_available_for_service("svc1")
        assert len(result) == 1
        assert result[0].window_id == "w1"

    def test_find_available_excludes_busy(self, window_repo):
        w = ServiceWindow("w1", "В1", ["svc1"], status=WindowStatus.OPEN, current_ticket_id="t1")
        window_repo.save(w)
        assert window_repo.find_available_for_service("svc1") == []

    def test_find_available_excludes_closed(self, window_repo):
        w = ServiceWindow("w1", "В1", ["svc1"], status=WindowStatus.CLOSED)
        window_repo.save(w)
        assert window_repo.find_available_for_service("svc1") == []

    def test_delete(self, window_repo):
        window_repo.save(ServiceWindow("w1", "В1"))
        assert window_repo.delete("w1") is True
        assert window_repo.find_by_id("w1") is None

    def test_delete_nonexistent(self, window_repo):
        assert window_repo.delete("ghost") is False

    def test_clear(self, window_repo):
        window_repo.save(ServiceWindow("w1", "В1"))
        window_repo.clear()
        assert window_repo.find_all() == []


# ─── Service Type Repository ───────────────────────────────────────────────────

class TestInMemoryServiceTypeRepository:
    def test_save_and_find(self, service_repo):
        s = ServiceType("s1", "Послуга 1")
        service_repo.save(s)
        assert service_repo.find_by_id("s1") is not None

    def test_find_active_only(self, service_repo):
        service_repo.save(ServiceType("s1", "Активна", is_active=True))
        service_repo.save(ServiceType("s2", "Неактивна", is_active=False))
        active = service_repo.find_active()
        assert len(active) == 1
        assert active[0].service_id == "s1"

    def test_find_all(self, service_repo):
        service_repo.save(ServiceType("s1", "S1"))
        service_repo.save(ServiceType("s2", "S2"))
        assert len(service_repo.find_all()) == 2

    def test_delete(self, service_repo):
        service_repo.save(ServiceType("s1", "S1"))
        assert service_repo.delete("s1") is True
        assert service_repo.find_by_id("s1") is None

    def test_find_not_found(self, service_repo):
        assert service_repo.find_by_id("ghost") is None

    def test_clear(self, service_repo):
        service_repo.save(ServiceType("s1", "S1"))
        service_repo.clear()
        assert service_repo.find_all() == []


# ─── Notification Repository ───────────────────────────────────────────────────

class TestInMemoryNotificationRepository:
    def test_save_and_find_by_ticket(self, notif_repo):
        n = Notification("n1", "t1", NotificationType.TICKET_CREATED, "msg")
        notif_repo.save(n)
        result = notif_repo.find_by_ticket_id("t1")
        assert len(result) == 1

    def test_find_unsent(self, notif_repo):
        notif_repo.save(Notification("n1", "t1", NotificationType.TICKET_CREATED, "msg", sent=False))
        notif_repo.save(Notification("n2", "t2", NotificationType.TICKET_CREATED, "msg", sent=True))
        unsent = notif_repo.find_unsent()
        assert len(unsent) == 1
        assert unsent[0].notification_id == "n1"

    def test_mark_sent(self, notif_repo):
        notif_repo.save(Notification("n1", "t1", NotificationType.TICKET_CREATED, "msg"))
        assert notif_repo.mark_sent("n1") is True
        assert notif_repo.find_by_ticket_id("t1")[0].sent is True

    def test_mark_sent_nonexistent(self, notif_repo):
        assert notif_repo.mark_sent("ghost") is False

    def test_find_all(self, notif_repo):
        notif_repo.save(Notification("n1", "t1", NotificationType.TICKET_CREATED, "m1"))
        notif_repo.save(Notification("n2", "t2", NotificationType.TICKET_COMPLETED, "m2"))
        assert len(notif_repo.find_all()) == 2

    def test_find_by_ticket_empty(self, notif_repo):
        assert notif_repo.find_by_ticket_id("ghost") == []

    def test_clear(self, notif_repo):
        notif_repo.save(Notification("n1", "t1", NotificationType.TICKET_CREATED, "msg"))
        notif_repo.clear()
        assert notif_repo.find_all() == []
