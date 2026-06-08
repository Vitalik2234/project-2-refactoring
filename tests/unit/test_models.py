import pytest
from datetime import datetime
from src.models import Ticket, TicketStatus, TicketPriority, ServiceWindow, WindowStatus, ServiceType, Notification, NotificationType


class TestTicketModel:
    def test_ticket_default_status(self):
        t = Ticket("id1", 1, "svc1")
        assert t.status == TicketStatus.WAITING

    def test_ticket_default_priority(self):
        t = Ticket("id1", 1, "svc1")
        assert t.priority == TicketPriority.NORMAL

    def test_ticket_to_dict_contains_required_keys(self):
        t = Ticket("id1", 1, "svc1")
        d = t.to_dict()
        for key in ("ticket_id", "number", "service_type", "status", "priority", "created_at"):
            assert key in d

    def test_ticket_to_dict_status_is_string(self):
        t = Ticket("id1", 1, "svc1")
        assert t.to_dict()["status"] == "waiting"

    def test_ticket_to_dict_priority_is_int(self):
        t = Ticket("id1", 1, "svc1", priority=TicketPriority.VIP)
        assert t.to_dict()["priority"] == 3

    def test_ticket_called_at_initially_none(self):
        t = Ticket("id1", 1, "svc1")
        assert t.called_at is None

    def test_ticket_completed_at_initially_none(self):
        t = Ticket("id1", 1, "svc1")
        assert t.completed_at is None

    def test_ticket_with_customer_name(self):
        t = Ticket("id1", 1, "svc1", customer_name="Іван")
        assert t.to_dict()["customer_name"] == "Іван"

    def test_ticket_with_phone(self):
        t = Ticket("id1", 1, "svc1", notification_phone="+380501234567")
        assert t.to_dict()["notification_phone"] == "+380501234567"

    def test_ticket_status_enum_values(self):
        assert TicketStatus.WAITING.value == "waiting"
        assert TicketStatus.CALLED.value == "called"
        assert TicketStatus.SERVING.value == "serving"
        assert TicketStatus.COMPLETED.value == "completed"
        assert TicketStatus.CANCELLED.value == "cancelled"
        assert TicketStatus.MISSED.value == "missed"

    def test_ticket_priority_enum_values(self):
        assert TicketPriority.NORMAL.value == 1
        assert TicketPriority.PRIORITY.value == 2
        assert TicketPriority.VIP.value == 3

    def test_ticket_estimated_wait_default(self):
        t = Ticket("id1", 1, "svc1")
        assert t.estimated_wait_minutes == 0

    def test_ticket_position_default(self):
        t = Ticket("id1", 1, "svc1")
        assert t.position_in_queue == 0

    def test_ticket_called_at_serialization(self):
        now = datetime.now()
        t = Ticket("id1", 1, "svc1", called_at=now)
        assert t.to_dict()["called_at"] == now.isoformat()

    def test_ticket_completed_at_serialization(self):
        now = datetime.now()
        t = Ticket("id1", 1, "svc1", completed_at=now)
        assert t.to_dict()["completed_at"] == now.isoformat()


class TestWindowModel:
    def test_window_default_status(self):
        w = ServiceWindow("w1", "Вікно 1", ["svc1"])
        assert w.status == WindowStatus.CLOSED

    def test_window_can_serve_when_open(self):
        w = ServiceWindow("w1", "Вікно 1", ["svc1"], status=WindowStatus.OPEN)
        assert w.can_serve("svc1") is True

    def test_window_cannot_serve_when_closed(self):
        w = ServiceWindow("w1", "Вікно 1", ["svc1"], status=WindowStatus.CLOSED)
        assert w.can_serve("svc1") is False

    def test_window_cannot_serve_wrong_type(self):
        w = ServiceWindow("w1", "Вікно 1", ["svc1"], status=WindowStatus.OPEN)
        assert w.can_serve("svc2") is False

    def test_window_to_dict_keys(self):
        w = ServiceWindow("w1", "Вікно 1")
        d = w.to_dict()
        for key in ("window_id", "name", "service_types", "status", "operator_name"):
            assert key in d

    def test_window_status_enum_values(self):
        assert WindowStatus.OPEN.value == "open"
        assert WindowStatus.CLOSED.value == "closed"
        assert WindowStatus.BREAK.value == "break"
        assert WindowStatus.BUSY.value == "busy"

    def test_window_to_dict_status_is_string(self):
        w = ServiceWindow("w1", "Вікно 1")
        assert w.to_dict()["status"] == "closed"

    def test_window_can_serve_break(self):
        w = ServiceWindow("w1", "Вікно 1", ["svc1"], status=WindowStatus.BREAK)
        assert w.can_serve("svc1") is False

    def test_window_can_serve_busy(self):
        w = ServiceWindow("w1", "Вікно 1", ["svc1"], status=WindowStatus.BUSY)
        assert w.can_serve("svc1") is False

    def test_window_multiple_service_types(self):
        w = ServiceWindow("w1", "Вікно 1", ["svc1", "svc2", "svc3"], status=WindowStatus.OPEN)
        assert w.can_serve("svc1")
        assert w.can_serve("svc2")
        assert w.can_serve("svc3")
        assert not w.can_serve("svc4")


class TestServiceTypeModel:
    def test_service_type_default_active(self):
        s = ServiceType("s1", "Послуга 1")
        assert s.is_active is True

    def test_service_type_to_dict(self):
        s = ServiceType("s1", "Послуга 1", "Опис", 7.0, "P")
        d = s.to_dict()
        assert d["service_id"] == "s1"
        assert d["name"] == "Послуга 1"
        assert d["avg_duration_minutes"] == 7.0
        assert d["prefix"] == "P"

    def test_service_type_default_duration(self):
        s = ServiceType("s1", "Послуга 1")
        assert s.avg_duration_minutes == 5.0

    def test_service_type_default_prefix(self):
        s = ServiceType("s1", "Послуга 1")
        assert s.prefix == "A"


class TestNotificationModel:
    def test_notification_not_sent_by_default(self):
        n = Notification("n1", "t1", NotificationType.TICKET_CREATED, "msg")
        assert n.sent is False

    def test_notification_to_dict(self):
        n = Notification("n1", "t1", NotificationType.CALLED_TO_WINDOW, "msg")
        d = n.to_dict()
        assert d["notification_id"] == "n1"
        assert d["ticket_id"] == "t1"
        assert d["type"] == "called_to_window"
        assert d["sent"] is False

    def test_notification_type_values(self):
        assert NotificationType.TICKET_CREATED.value == "ticket_created"
        assert NotificationType.CALLED_TO_WINDOW.value == "called_to_window"
        assert NotificationType.TURN_SOON.value == "turn_soon"
        assert NotificationType.TICKET_CANCELLED.value == "ticket_cancelled"
        assert NotificationType.TICKET_MISSED.value == "ticket_missed"
        assert NotificationType.TICKET_COMPLETED.value == "ticket_completed"
