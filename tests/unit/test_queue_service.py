import pytest
from unittest.mock import MagicMock
from src.models import TicketStatus, TicketPriority
from src.utils.strategies import FifoStrategy, PriorityStrategy, ShortestJobFirstStrategy


class TestQueueServiceIssueTicket:
    def test_issue_ticket_returns_ticket(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        assert t is not None
        assert t.ticket_id

    def test_issue_ticket_status_waiting(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        assert t.status == TicketStatus.WAITING

    def test_issue_ticket_increments_number(self, queue_service, sample_service):
        t1 = queue_service.issue_ticket(sample_service.service_id)
        t2 = queue_service.issue_ticket(sample_service.service_id)
        assert t2.number == t1.number + 1

    def test_issue_ticket_invalid_service(self, queue_service):
        with pytest.raises(ValueError):
            queue_service.issue_ticket("nonexistent_svc")

    def test_issue_ticket_inactive_service(self, queue_service, service_type_service, sample_service):
        service_type_service.deactivate(sample_service.service_id)
        with pytest.raises(ValueError):
            queue_service.issue_ticket(sample_service.service_id)

    def test_issue_ticket_with_name(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id, customer_name="Олена")
        assert t.customer_name == "Олена"

    def test_issue_ticket_with_phone(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id, notification_phone="+380501234567")
        assert t.notification_phone == "+380501234567"

    def test_issue_ticket_vip_priority(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id, priority=TicketPriority.VIP)
        assert t.priority == TicketPriority.VIP

    def test_issue_ticket_calculates_wait(self, queue_service, sample_service):
        queue_service.issue_ticket(sample_service.service_id)
        t2 = queue_service.issue_ticket(sample_service.service_id)
        assert t2.estimated_wait_minutes > 0

    def test_issue_ticket_position(self, queue_service, sample_service):
        t1 = queue_service.issue_ticket(sample_service.service_id)
        t2 = queue_service.issue_ticket(sample_service.service_id)
        assert t1.position_in_queue == 1
        assert t2.position_in_queue == 2

    def test_issue_ticket_triggers_observer(self, queue_service, sample_service):
        obs = MagicMock()
        queue_service.add_observer(obs)
        queue_service.issue_ticket(sample_service.service_id)
        obs.on_ticket_created.assert_called_once()

    def test_issue_multiple_services(self, queue_service, service_type_service):
        s1 = service_type_service.create_service("S1", "", 5.0, "A")
        s2 = service_type_service.create_service("S2", "", 5.0, "B")
        t1 = queue_service.issue_ticket(s1.service_id)
        t2 = queue_service.issue_ticket(s2.service_id)
        assert t1.number == 1
        assert t2.number == 1  # independent counters


class TestQueueServiceGetQueue:
    def test_get_queue_empty(self, queue_service):
        assert queue_service.get_queue() == []

    def test_get_queue_returns_waiting(self, queue_service, sample_service):
        queue_service.issue_ticket(sample_service.service_id)
        assert len(queue_service.get_queue()) == 1

    def test_get_queue_filters_by_service(self, queue_service, service_type_service):
        s1 = service_type_service.create_service("S1", "", 5.0, "A")
        s2 = service_type_service.create_service("S2", "", 5.0, "B")
        queue_service.issue_ticket(s1.service_id)
        queue_service.issue_ticket(s2.service_id)
        assert len(queue_service.get_queue(s1.service_id)) == 1

    def test_get_queue_not_includes_completed(self, queue_service, sample_service, sample_window, window_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        queue_service.call_next(sample_service.service_id, sample_window.window_id, sample_window.name)
        queue_service.complete_ticket(t.ticket_id)
        assert queue_service.get_queue() == []

    def test_get_queue_not_includes_cancelled(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        queue_service.cancel_ticket(t.ticket_id)
        assert queue_service.get_queue() == []


class TestQueueServiceCallNext:
    def test_call_next_returns_ticket(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        assert t is not None

    def test_call_next_changes_status(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        assert t.status == TicketStatus.CALLED

    def test_call_next_empty_queue(self, queue_service, sample_service, sample_window):
        result = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        assert result is None

    def test_call_next_sets_window_id(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        assert t.window_id == sample_window.window_id

    def test_call_next_sets_called_at(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        assert t.called_at is not None

    def test_call_next_notifies_observer(self, queue_service, sample_service, sample_window):
        obs = MagicMock()
        queue_service.add_observer(obs)
        queue_service.issue_ticket(sample_service.service_id)
        queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        obs.on_ticket_called.assert_called_once()

    def test_call_next_calls_first_in_fifo(self, queue_service, sample_service, sample_window):
        t1 = queue_service.issue_ticket(sample_service.service_id)
        queue_service.issue_ticket(sample_service.service_id)
        called = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        assert called.ticket_id == t1.ticket_id


class TestQueueServiceComplete:
    def test_complete_ticket(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        completed = queue_service.complete_ticket(t.ticket_id)
        assert completed.status == TicketStatus.COMPLETED

    def test_complete_sets_completed_at(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        completed = queue_service.complete_ticket(t.ticket_id)
        assert completed.completed_at is not None

    def test_complete_nonexistent_ticket(self, queue_service):
        with pytest.raises(ValueError):
            queue_service.complete_ticket("ghost")

    def test_complete_waiting_ticket_raises(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        with pytest.raises(ValueError):
            queue_service.complete_ticket(t.ticket_id)

    def test_complete_notifies_observer(self, queue_service, sample_service, sample_window):
        obs = MagicMock()
        queue_service.add_observer(obs)
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        queue_service.complete_ticket(t.ticket_id)
        obs.on_ticket_completed.assert_called_once()


class TestQueueServiceCancel:
    def test_cancel_waiting_ticket(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        cancelled = queue_service.cancel_ticket(t.ticket_id)
        assert cancelled.status == TicketStatus.CANCELLED

    def test_cancel_nonexistent(self, queue_service):
        with pytest.raises(ValueError):
            queue_service.cancel_ticket("ghost")

    def test_cancel_already_cancelled(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        queue_service.cancel_ticket(t.ticket_id)
        with pytest.raises(ValueError):
            queue_service.cancel_ticket(t.ticket_id)

    def test_cancel_completed_raises(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        queue_service.complete_ticket(t.ticket_id)
        with pytest.raises(ValueError):
            queue_service.cancel_ticket(t.ticket_id)

    def test_cancel_notifies_observer(self, queue_service, sample_service):
        obs = MagicMock()
        queue_service.add_observer(obs)
        t = queue_service.issue_ticket(sample_service.service_id)
        queue_service.cancel_ticket(t.ticket_id)
        obs.on_ticket_cancelled.assert_called_once()


class TestQueueServiceMiss:
    def test_mark_missed(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        missed = queue_service.mark_missed(t.ticket_id)
        assert missed.status == TicketStatus.MISSED

    def test_mark_missed_waiting_raises(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        with pytest.raises(ValueError):
            queue_service.mark_missed(t.ticket_id)

    def test_mark_missed_notifies(self, queue_service, sample_service, sample_window):
        obs = MagicMock()
        queue_service.add_observer(obs)
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        queue_service.mark_missed(t.ticket_id)
        obs.on_ticket_missed.assert_called_once()

    def test_mark_missed_nonexistent(self, queue_service):
        with pytest.raises(ValueError):
            queue_service.mark_missed("ghost")


class TestQueueServiceStats:
    def test_stats_empty(self, queue_service):
        stats = queue_service.get_queue_stats()
        assert stats["total"] == 0
        assert stats["waiting"] == 0

    def test_stats_counts(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        queue_service.issue_ticket(sample_service.service_id)
        t3 = queue_service.issue_ticket(sample_service.service_id)
        queue_service.cancel_ticket(t3.ticket_id)
        stats = queue_service.get_queue_stats()
        assert stats["waiting"] == 2
        assert stats["cancelled"] == 1
        assert stats["total"] == 3


class TestQueueServiceStrategy:
    def test_set_strategy(self, queue_service):
        queue_service.set_strategy(PriorityStrategy())
        assert queue_service.get_strategy_name() == "PRIORITY"

    def test_priority_strategy_orders_vip_first(self, queue_service, sample_service):
        queue_service.set_strategy(PriorityStrategy())
        t_normal = queue_service.issue_ticket(sample_service.service_id, priority=TicketPriority.NORMAL)
        t_vip = queue_service.issue_ticket(sample_service.service_id, priority=TicketPriority.VIP)
        queue = queue_service.get_queue()
        assert queue[0].ticket_id == t_vip.ticket_id

    def test_fifo_default_strategy(self, queue_service):
        assert queue_service.get_strategy_name() == "FIFO"

    def test_sjf_strategy_name(self, queue_service):
        queue_service.set_strategy(ShortestJobFirstStrategy())
        assert queue_service.get_strategy_name() == "SJF"


class TestQueueServicePosition:
    def test_get_position_first(self, queue_service, sample_service):
        t = queue_service.issue_ticket(sample_service.service_id)
        pos, wait = queue_service.get_position(t.ticket_id)
        assert pos == 1

    def test_get_position_second(self, queue_service, sample_service):
        queue_service.issue_ticket(sample_service.service_id)
        t2 = queue_service.issue_ticket(sample_service.service_id)
        pos, _ = queue_service.get_position(t2.ticket_id)
        assert pos == 2

    def test_get_position_not_in_queue(self, queue_service):
        pos, wait = queue_service.get_position("ghost")
        assert pos == 0
        assert wait == 0

    def test_get_position_called_ticket(self, queue_service, sample_service, sample_window):
        queue_service.issue_ticket(sample_service.service_id)
        t = queue_service.call_next(sample_service.service_id, sample_window.window_id, "В1")
        pos, _ = queue_service.get_position(t.ticket_id)
        assert pos == 0
