import pytest
from datetime import datetime, timedelta
from src.models import Ticket, TicketPriority, TicketStatus
from src.utils.strategies import FifoStrategy, PriorityStrategy, ShortestJobFirstStrategy
from src.utils.observers import NotificationObserver, LoggingObserver
from src.storage.in_memory import InMemoryNotificationRepository


def make_ticket(ticket_id, number, service="svc1", priority=TicketPriority.NORMAL,
                created_offset_seconds=0, estimated_wait=5):
    t = Ticket(ticket_id, number, service, priority=priority,
               estimated_wait_minutes=estimated_wait)
    t.created_at = datetime.now() + timedelta(seconds=created_offset_seconds)
    return t


class TestFifoStrategy:
    def test_fifo_empty(self):
        assert FifoStrategy().sort([]) == []

    def test_fifo_single(self):
        t = make_ticket("t1", 1)
        assert FifoStrategy().sort([t]) == [t]

    def test_fifo_orders_by_time(self):
        t1 = make_ticket("t1", 1, created_offset_seconds=0)
        t2 = make_ticket("t2", 2, created_offset_seconds=5)
        t3 = make_ticket("t3", 3, created_offset_seconds=10)
        result = FifoStrategy().sort([t3, t1, t2])
        assert [t.ticket_id for t in result] == ["t1", "t2", "t3"]

    def test_fifo_same_time(self):
        now = datetime.now()
        t1 = Ticket("t1", 1, "svc1")
        t2 = Ticket("t2", 2, "svc1")
        t1.created_at = now
        t2.created_at = now
        result = FifoStrategy().sort([t1, t2])
        assert len(result) == 2

    def test_fifo_name(self):
        assert FifoStrategy().get_name() == "FIFO"

    def test_fifo_does_not_mutate_input(self):
        tickets = [make_ticket(f"t{i}", i, created_offset_seconds=i*10) for i in range(5)]
        original_ids = [t.ticket_id for t in tickets]
        FifoStrategy().sort(tickets)
        assert [t.ticket_id for t in tickets] == original_ids


class TestPriorityStrategy:
    def test_priority_empty(self):
        assert PriorityStrategy().sort([]) == []

    def test_priority_vip_first(self):
        t_normal = make_ticket("t1", 1, priority=TicketPriority.NORMAL)
        t_vip = make_ticket("t2", 2, priority=TicketPriority.VIP)
        result = PriorityStrategy().sort([t_normal, t_vip])
        assert result[0].ticket_id == "t2"

    def test_priority_order(self):
        t_normal = make_ticket("t1", 1, priority=TicketPriority.NORMAL)
        t_prio = make_ticket("t2", 2, priority=TicketPriority.PRIORITY)
        t_vip = make_ticket("t3", 3, priority=TicketPriority.VIP)
        result = PriorityStrategy().sort([t_normal, t_prio, t_vip])
        assert result[0].priority == TicketPriority.VIP
        assert result[1].priority == TicketPriority.PRIORITY
        assert result[2].priority == TicketPriority.NORMAL

    def test_priority_same_priority_fifo(self):
        t1 = make_ticket("t1", 1, priority=TicketPriority.VIP, created_offset_seconds=0)
        t2 = make_ticket("t2", 2, priority=TicketPriority.VIP, created_offset_seconds=10)
        result = PriorityStrategy().sort([t2, t1])
        assert result[0].ticket_id == "t1"

    def test_priority_name(self):
        assert PriorityStrategy().get_name() == "PRIORITY"

    def test_priority_single(self):
        t = make_ticket("t1", 1, priority=TicketPriority.VIP)
        assert PriorityStrategy().sort([t]) == [t]


class TestShortestJobFirstStrategy:
    def test_sjf_empty(self):
        assert ShortestJobFirstStrategy().sort([]) == []

    def test_sjf_orders_by_wait(self):
        t1 = make_ticket("t1", 1, estimated_wait=15)
        t2 = make_ticket("t2", 2, estimated_wait=5)
        t3 = make_ticket("t3", 3, estimated_wait=10)
        result = ShortestJobFirstStrategy().sort([t1, t2, t3])
        assert result[0].ticket_id == "t2"
        assert result[1].ticket_id == "t3"
        assert result[2].ticket_id == "t1"

    def test_sjf_single(self):
        t = make_ticket("t1", 1, estimated_wait=7)
        assert ShortestJobFirstStrategy().sort([t]) == [t]

    def test_sjf_name(self):
        assert ShortestJobFirstStrategy().get_name() == "SJF"

    def test_sjf_zero_wait(self):
        t1 = make_ticket("t1", 1, estimated_wait=0)
        t2 = make_ticket("t2", 2, estimated_wait=5)
        result = ShortestJobFirstStrategy().sort([t1, t2])
        assert result[0].ticket_id == "t1"


class TestNotificationObserver:
    def setup_method(self):
        self.repo = InMemoryNotificationRepository()
        self.obs = NotificationObserver(self.repo)

    def _make_ticket(self):
        return Ticket("t1", 1, "svc1", customer_name="Тест", notification_phone="+380")

    def test_on_created_saves_notification(self):
        self.obs.on_ticket_created(self._make_ticket())
        assert len(self.repo.find_all()) == 1

    def test_on_created_correct_type(self):
        from src.models import NotificationType
        self.obs.on_ticket_created(self._make_ticket())
        n = self.repo.find_all()[0]
        assert n.notification_type == NotificationType.TICKET_CREATED

    def test_on_called_saves_notification(self):
        self.obs.on_ticket_called(self._make_ticket(), "Вікно 1")
        assert len(self.repo.find_all()) == 1

    def test_on_called_correct_type(self):
        from src.models import NotificationType
        self.obs.on_ticket_called(self._make_ticket(), "Вікно 1")
        n = self.repo.find_all()[0]
        assert n.notification_type == NotificationType.CALLED_TO_WINDOW

    def test_on_completed_saves_notification(self):
        self.obs.on_ticket_completed(self._make_ticket())
        assert len(self.repo.find_all()) == 1

    def test_on_cancelled_saves_notification(self):
        self.obs.on_ticket_cancelled(self._make_ticket())
        assert len(self.repo.find_all()) == 1

    def test_on_missed_saves_notification(self):
        self.obs.on_ticket_missed(self._make_ticket())
        assert len(self.repo.find_all()) == 1

    def test_notification_linked_to_ticket(self):
        t = self._make_ticket()
        self.obs.on_ticket_created(t)
        n = self.repo.find_all()[0]
        assert n.ticket_id == "t1"

    def test_notification_not_sent_by_default(self):
        self.obs.on_ticket_created(self._make_ticket())
        n = self.repo.find_all()[0]
        assert n.sent is False

    def test_notification_message_contains_number(self):
        self.obs.on_ticket_created(self._make_ticket())
        n = self.repo.find_all()[0]
        assert "1" in n.message

    def test_called_message_contains_window(self):
        self.obs.on_ticket_called(self._make_ticket(), "Вікно 3")
        n = self.repo.find_all()[0]
        assert "Вікно 3" in n.message

    def test_multiple_events_multiple_notifications(self):
        t = self._make_ticket()
        self.obs.on_ticket_created(t)
        self.obs.on_ticket_called(t, "В1")
        self.obs.on_ticket_completed(t)
        assert len(self.repo.find_all()) == 3


class TestLoggingObserver:
    def setup_method(self):
        self.obs = LoggingObserver()

    def _make_ticket(self):
        return Ticket("t1", 1, "svc1")

    def test_initially_empty(self):
        assert self.obs.get_events() == []

    def test_created_event_logged(self):
        self.obs.on_ticket_created(self._make_ticket())
        events = self.obs.get_events()
        assert len(events) == 1
        assert events[0]["event"] == "created"

    def test_called_event_logged(self):
        self.obs.on_ticket_called(self._make_ticket(), "В1")
        events = self.obs.get_events()
        assert events[0]["event"] == "called"
        assert events[0]["window"] == "В1"

    def test_completed_event_logged(self):
        self.obs.on_ticket_completed(self._make_ticket())
        assert self.obs.get_events()[0]["event"] == "completed"

    def test_cancelled_event_logged(self):
        self.obs.on_ticket_cancelled(self._make_ticket())
        assert self.obs.get_events()[0]["event"] == "cancelled"

    def test_missed_event_logged(self):
        self.obs.on_ticket_missed(self._make_ticket())
        assert self.obs.get_events()[0]["event"] == "missed"

    def test_multiple_events(self):
        t = self._make_ticket()
        self.obs.on_ticket_created(t)
        self.obs.on_ticket_called(t, "В1")
        self.obs.on_ticket_completed(t)
        assert len(self.obs.get_events()) == 3

    def test_event_has_ticket_id(self):
        self.obs.on_ticket_created(self._make_ticket())
        assert self.obs.get_events()[0]["ticket_id"] == "t1"

    def test_event_has_time(self):
        self.obs.on_ticket_created(self._make_ticket())
        assert "time" in self.obs.get_events()[0]

    def test_get_events_returns_copy(self):
        self.obs.on_ticket_created(self._make_ticket())
        events = self.obs.get_events()
        events.clear()
        assert len(self.obs.get_events()) == 1
