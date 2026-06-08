import pytest
from src.models import TicketStatus, TicketPriority, WindowStatus, NotificationType


class TestFullQueueFlow:
    """End-to-end integration tests for the complete queue lifecycle."""

    def test_full_lifecycle_issue_call_complete(self, full_setup):
        q = full_setup["queue"]
        w = full_setup["windows"]
        s = full_setup["service"]
        win = full_setup["window"]

        # Issue
        ticket = q.issue_ticket(s.service_id, customer_name="Олена")
        assert ticket.status == TicketStatus.WAITING

        # Call next
        called = q.call_next(s.service_id, win.window_id, win.name)
        assert called.ticket_id == ticket.ticket_id
        assert called.status == TicketStatus.CALLED

        # Assign window
        w.assign_ticket(win.window_id, called.ticket_id)
        window = w.get_window(win.window_id)
        assert window.status == WindowStatus.BUSY

        # Complete
        completed = q.complete_ticket(called.ticket_id)
        assert completed.status == TicketStatus.COMPLETED

        # Free window
        freed = w.free_window(win.window_id)
        assert freed.status == WindowStatus.OPEN
        assert freed.tickets_served_today == 1

    def test_full_lifecycle_issue_call_miss(self, full_setup):
        q = full_setup["queue"]
        w = full_setup["windows"]
        s = full_setup["service"]
        win = full_setup["window"]

        ticket = q.issue_ticket(s.service_id)
        called = q.call_next(s.service_id, win.window_id, win.name)
        missed = q.mark_missed(called.ticket_id)
        assert missed.status == TicketStatus.MISSED

        w.free_window(win.window_id)
        assert w.get_window(win.window_id).status == WindowStatus.OPEN

    def test_full_lifecycle_cancel(self, full_setup):
        q = full_setup["queue"]
        s = full_setup["service"]

        ticket = q.issue_ticket(s.service_id)
        cancelled = q.cancel_ticket(ticket.ticket_id)
        assert cancelled.status == TicketStatus.CANCELLED
        assert q.get_queue() == []

    def test_notifications_created_on_lifecycle(self, full_setup):
        q = full_setup["queue"]
        notif = full_setup["notifications"]
        s = full_setup["service"]
        win = full_setup["window"]

        ticket = q.issue_ticket(s.service_id)
        q.call_next(s.service_id, win.window_id, win.name)
        q.complete_ticket(ticket.ticket_id)

        all_notifs = notif.get_all()
        types = [n.notification_type for n in all_notifs]
        assert NotificationType.TICKET_CREATED in types
        assert NotificationType.CALLED_TO_WINDOW in types
        assert NotificationType.TICKET_COMPLETED in types

    def test_multiple_tickets_queue_order(self, full_setup):
        q = full_setup["queue"]
        s = full_setup["service"]
        win = full_setup["window"]

        t1 = q.issue_ticket(s.service_id)
        t2 = q.issue_ticket(s.service_id)
        t3 = q.issue_ticket(s.service_id)

        assert len(q.get_queue()) == 3

        called1 = q.call_next(s.service_id, win.window_id, win.name)
        assert called1.ticket_id == t1.ticket_id

        q.complete_ticket(called1.ticket_id)
        full_setup["windows"].free_window(win.window_id)

        called2 = q.call_next(s.service_id, win.window_id, win.name)
        assert called2.ticket_id == t2.ticket_id

    def test_priority_ticket_served_first(self, full_setup):
        from src.utils.strategies import PriorityStrategy
        q = full_setup["queue"]
        s = full_setup["service"]
        win = full_setup["window"]

        q.set_strategy(PriorityStrategy())
        t_normal = q.issue_ticket(s.service_id, priority=TicketPriority.NORMAL)
        t_vip = q.issue_ticket(s.service_id, priority=TicketPriority.VIP)

        called = q.call_next(s.service_id, win.window_id, win.name)
        assert called.ticket_id == t_vip.ticket_id

    def test_logging_observer_captures_all_events(self, full_setup):
        q = full_setup["queue"]
        s = full_setup["service"]
        win = full_setup["window"]
        log = full_setup["log_obs"]

        t = q.issue_ticket(s.service_id)
        q.call_next(s.service_id, win.window_id, win.name)
        q.complete_ticket(t.ticket_id)

        events = log.get_events()
        event_types = [e["event"] for e in events]
        assert "created" in event_types
        assert "called" in event_types
        assert "completed" in event_types

    def test_stats_reflect_full_flow(self, full_setup):
        q = full_setup["queue"]
        s = full_setup["service"]
        win = full_setup["window"]

        q.issue_ticket(s.service_id)
        q.issue_ticket(s.service_id)
        t3 = q.issue_ticket(s.service_id)
        q.cancel_ticket(t3.ticket_id)

        t = q.call_next(s.service_id, win.window_id, win.name)
        q.complete_ticket(t.ticket_id)

        stats = q.get_queue_stats()
        assert stats["waiting"] == 1
        assert stats["completed"] == 1
        assert stats["cancelled"] == 1

    def test_window_serves_multiple_tickets(self, full_setup):
        q = full_setup["queue"]
        w = full_setup["windows"]
        s = full_setup["service"]
        win = full_setup["window"]

        for _ in range(5):
            q.issue_ticket(s.service_id)

        served = 0
        for _ in range(5):
            ticket = q.call_next(s.service_id, win.window_id, win.name)
            if ticket:
                w.assign_ticket(win.window_id, ticket.ticket_id)
                q.complete_ticket(ticket.ticket_id)
                w.free_window(win.window_id)
                served += 1

        assert served == 5
        window = w.get_window(win.window_id)
        assert window.tickets_served_today == 5

    def test_notification_process_pending(self, full_setup):
        q = full_setup["queue"]
        notif = full_setup["notifications"]
        s = full_setup["service"]

        q.issue_ticket(s.service_id)
        q.issue_ticket(s.service_id)

        unsent_before = len(notif.get_unsent())
        assert unsent_before == 2

        processed = notif.process_pending()
        assert processed == 2
        assert notif.get_unsent() == []

    def test_call_specific_ticket(self, full_setup):
        q = full_setup["queue"]
        s = full_setup["service"]
        win = full_setup["window"]

        q.issue_ticket(s.service_id)
        t2 = q.issue_ticket(s.service_id)
        q.issue_ticket(s.service_id)

        called = q.call_specific(t2.ticket_id, win.window_id, win.name)
        assert called.ticket_id == t2.ticket_id
        assert called.status == TicketStatus.CALLED

    def test_mixed_services_independent_queues(self, full_setup):
        q = full_setup["queue"]
        svcs = full_setup["services"]
        s1 = full_setup["service"]
        s2 = svcs.create_service("Друга", "Опис", 5.0, "D")

        q.issue_ticket(s1.service_id)
        q.issue_ticket(s1.service_id)
        q.issue_ticket(s2.service_id)

        queue_s1 = q.get_queue(s1.service_id)
        queue_s2 = q.get_queue(s2.service_id)
        assert len(queue_s1) == 2
        assert len(queue_s2) == 1

    def test_position_decreases_after_call(self, full_setup):
        q = full_setup["queue"]
        s = full_setup["service"]
        win = full_setup["window"]

        q.issue_ticket(s.service_id)
        t2 = q.issue_ticket(s.service_id)

        pos_before, _ = q.get_position(t2.ticket_id)
        assert pos_before == 2

        q.call_next(s.service_id, win.window_id, win.name)

        pos_after, _ = q.get_position(t2.ticket_id)
        assert pos_after == 1

    def test_empty_queue_after_all_completed(self, full_setup):
        q = full_setup["queue"]
        s = full_setup["service"]
        win = full_setup["window"]

        tickets = [q.issue_ticket(s.service_id) for _ in range(3)]
        for _ in tickets:
            called = q.call_next(s.service_id, win.window_id, win.name)
            q.complete_ticket(called.ticket_id)
            full_setup["windows"].free_window(win.window_id)

        assert q.get_queue() == []
        assert q.get_queue_stats()["completed"] == 3

    def test_cancelled_ticket_not_called(self, full_setup):
        q = full_setup["queue"]
        s = full_setup["service"]
        win = full_setup["window"]

        t1 = q.issue_ticket(s.service_id)
        q.cancel_ticket(t1.ticket_id)

        result = q.call_next(s.service_id, win.window_id, win.name)
        assert result is None

    def test_strategy_can_be_switched_mid_queue(self, full_setup):
        from src.utils.strategies import PriorityStrategy, FifoStrategy
        q = full_setup["queue"]
        s = full_setup["service"]

        q.issue_ticket(s.service_id, priority=TicketPriority.NORMAL)
        q.issue_ticket(s.service_id, priority=TicketPriority.VIP)

        q.set_strategy(PriorityStrategy())
        queue = q.get_queue()
        assert queue[0].priority == TicketPriority.VIP

        q.set_strategy(FifoStrategy())
        queue = q.get_queue()
        assert queue[0].priority == TicketPriority.NORMAL
