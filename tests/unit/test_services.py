import pytest
from src.models import WindowStatus


class TestWindowService:
    def test_create_window(self, window_service, sample_service):
        w = window_service.create_window("Вікно 1", [sample_service.service_id])
        assert w.window_id is not None
        assert w.name == "Вікно 1"

    def test_create_window_empty_name_raises(self, window_service):
        with pytest.raises(ValueError):
            window_service.create_window("", ["svc1"])

    def test_create_window_no_services_raises(self, window_service):
        with pytest.raises(ValueError):
            window_service.create_window("В1", [])

    def test_window_default_closed(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        assert w.status == WindowStatus.CLOSED

    def test_open_window(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        opened = window_service.open_window(w.window_id)
        assert opened.status == WindowStatus.OPEN

    def test_close_window(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        window_service.open_window(w.window_id)
        closed = window_service.close_window(w.window_id)
        assert closed.status == WindowStatus.CLOSED

    def test_set_break(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        window_service.open_window(w.window_id)
        b = window_service.set_break(w.window_id)
        assert b.status == WindowStatus.BREAK

    def test_assign_ticket_to_open_window(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        window_service.open_window(w.window_id)
        assigned = window_service.assign_ticket(w.window_id, "ticket123")
        assert assigned.current_ticket_id == "ticket123"
        assert assigned.status == WindowStatus.BUSY

    def test_assign_ticket_to_closed_raises(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        with pytest.raises(ValueError):
            window_service.assign_ticket(w.window_id, "t1")

    def test_free_window(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        window_service.open_window(w.window_id)
        window_service.assign_ticket(w.window_id, "t1")
        freed = window_service.free_window(w.window_id)
        assert freed.current_ticket_id is None
        assert freed.status == WindowStatus.OPEN

    def test_free_increments_served_count(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        window_service.open_window(w.window_id)
        window_service.assign_ticket(w.window_id, "t1")
        freed = window_service.free_window(w.window_id)
        assert freed.tickets_served_today == 1

    def test_get_all_windows(self, window_service, sample_service):
        window_service.create_window("В1", [sample_service.service_id])
        window_service.create_window("В2", [sample_service.service_id])
        assert len(window_service.get_all_windows()) == 2

    def test_get_window_by_id(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        found = window_service.get_window(w.window_id)
        assert found.window_id == w.window_id

    def test_get_window_not_found(self, window_service):
        assert window_service.get_window("ghost") is None

    def test_get_available_windows(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        window_service.open_window(w.window_id)
        available = window_service.get_available_windows(sample_service.service_id)
        assert len(available) == 1

    def test_delete_window(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        assert window_service.delete_window(w.window_id) is True
        assert window_service.get_window(w.window_id) is None

    def test_delete_nonexistent_window(self, window_service):
        with pytest.raises(ValueError):
            window_service.delete_window("ghost")

    def test_open_nonexistent_raises(self, window_service):
        with pytest.raises(ValueError):
            window_service.open_window("ghost")

    def test_close_nonexistent_raises(self, window_service):
        with pytest.raises(ValueError):
            window_service.close_window("ghost")

    def test_close_clears_ticket(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id])
        window_service.open_window(w.window_id)
        window_service.assign_ticket(w.window_id, "t1")
        closed = window_service.close_window(w.window_id)
        assert closed.current_ticket_id is None

    def test_operator_name(self, window_service, sample_service):
        w = window_service.create_window("В1", [sample_service.service_id], operator_name="Олена")
        assert w.operator_name == "Олена"


class TestServiceTypeService:
    def test_create_service(self, service_type_service):
        s = service_type_service.create_service("Консультація", "Опис", 10.0, "K")
        assert s.service_id is not None
        assert s.name == "Консультація"

    def test_create_service_empty_name_raises(self, service_type_service):
        with pytest.raises(ValueError):
            service_type_service.create_service("")

    def test_create_service_zero_duration_raises(self, service_type_service):
        with pytest.raises(ValueError):
            service_type_service.create_service("S1", avg_duration=0)

    def test_create_service_negative_duration_raises(self, service_type_service):
        with pytest.raises(ValueError):
            service_type_service.create_service("S1", avg_duration=-1.0)

    def test_service_active_by_default(self, service_type_service):
        s = service_type_service.create_service("S1")
        assert s.is_active is True

    def test_deactivate_service(self, service_type_service):
        s = service_type_service.create_service("S1")
        deactivated = service_type_service.deactivate(s.service_id)
        assert deactivated.is_active is False

    def test_activate_service(self, service_type_service):
        s = service_type_service.create_service("S1")
        service_type_service.deactivate(s.service_id)
        activated = service_type_service.activate(s.service_id)
        assert activated.is_active is True

    def test_get_active_only(self, service_type_service):
        service_type_service.create_service("S1")
        s2 = service_type_service.create_service("S2")
        service_type_service.deactivate(s2.service_id)
        active = service_type_service.get_active()
        assert len(active) == 1

    def test_get_all(self, service_type_service):
        service_type_service.create_service("S1")
        service_type_service.create_service("S2")
        assert len(service_type_service.get_all()) == 2

    def test_get_by_id(self, service_type_service):
        s = service_type_service.create_service("S1")
        found = service_type_service.get_by_id(s.service_id)
        assert found.service_id == s.service_id

    def test_delete(self, service_type_service):
        s = service_type_service.create_service("S1")
        assert service_type_service.delete(s.service_id) is True
        assert service_type_service.get_by_id(s.service_id) is None

    def test_delete_nonexistent(self, service_type_service):
        with pytest.raises(ValueError):
            service_type_service.delete("ghost")

    def test_deactivate_nonexistent(self, service_type_service):
        with pytest.raises(ValueError):
            service_type_service.deactivate("ghost")

    def test_prefix_stored(self, service_type_service):
        s = service_type_service.create_service("S1", prefix="X")
        assert s.prefix == "X"


class TestNotificationService:
    def test_get_all_empty(self, notification_service):
        assert notification_service.get_all() == []

    def test_get_unsent_empty(self, notification_service):
        assert notification_service.get_unsent() == []

    def test_process_pending_returns_count(self, notification_service, notif_repo):
        from src.models import Notification, NotificationType
        notif_repo.save(Notification("n1", "t1", NotificationType.TICKET_CREATED, "msg"))
        notif_repo.save(Notification("n2", "t2", NotificationType.TICKET_CREATED, "msg"))
        count = notification_service.process_pending()
        assert count == 2

    def test_process_pending_marks_sent(self, notification_service, notif_repo):
        from src.models import Notification, NotificationType
        notif_repo.save(Notification("n1", "t1", NotificationType.TICKET_CREATED, "msg"))
        notification_service.process_pending()
        assert notification_service.get_unsent() == []

    def test_get_for_ticket(self, notification_service, notif_repo):
        from src.models import Notification, NotificationType
        notif_repo.save(Notification("n1", "t1", NotificationType.TICKET_CREATED, "msg"))
        result = notification_service.get_for_ticket("t1")
        assert len(result) == 1
