import pytest
import json
from app import app as flask_app
from src.utils.container import reset_container, get_container


@pytest.fixture(autouse=True)
def reset_state():
    """Reset container before each test for isolation."""
    reset_container()
    yield
    reset_container()


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def setup(client):
    """Helper: create a service and open window via API."""
    c = get_container()
    svc = c.service_type_service.create_service("Тест", "Опис", 5.0, "T")
    win = c.window_service.create_window("Вікно 1", [svc.service_id], "Оператор")
    c.window_service.open_window(win.window_id)
    return {"service_id": svc.service_id, "window_id": win.window_id}


class TestIndexPage:
    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_kiosk_returns_200(self, client):
        r = client.get("/kiosk")
        assert r.status_code == 200

    def test_display_returns_200(self, client):
        r = client.get("/display")
        assert r.status_code == 200


class TestTicketAPI:
    def test_issue_ticket(self, client, setup):
        r = client.post("/api/tickets", json={"service_type": setup["service_id"]})
        assert r.status_code == 201
        data = r.get_json()
        assert data["ok"] is True
        assert data["ticket"]["number"] == 1

    def test_issue_ticket_invalid_service(self, client):
        r = client.post("/api/tickets", json={"service_type": "ghost"})
        assert r.status_code == 400
        assert r.get_json()["ok"] is False

    def test_issue_ticket_with_name(self, client, setup):
        r = client.post("/api/tickets", json={"service_type": setup["service_id"], "customer_name": "Марія"})
        assert r.get_json()["ticket"]["customer_name"] == "Марія"

    def test_issue_ticket_with_priority(self, client, setup):
        r = client.post("/api/tickets", json={"service_type": setup["service_id"], "priority": 3})
        assert r.get_json()["ticket"]["priority"] == 3

    def test_list_tickets_empty(self, client):
        r = client.get("/api/tickets")
        data = r.get_json()
        assert data["ok"] is True
        assert data["tickets"] == []

    def test_list_tickets_after_issue(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        r = client.get("/api/tickets")
        assert len(r.get_json()["tickets"]) == 1

    def test_get_ticket_by_id(self, client, setup):
        issued = client.post("/api/tickets", json={"service_type": setup["service_id"]}).get_json()
        ticket_id = issued["ticket"]["ticket_id"]
        r = client.get(f"/api/tickets/{ticket_id}")
        assert r.status_code == 200
        assert r.get_json()["ticket"]["ticket_id"] == ticket_id

    def test_get_ticket_not_found(self, client):
        r = client.get("/api/tickets/ghost")
        assert r.status_code == 404

    def test_cancel_ticket(self, client, setup):
        issued = client.post("/api/tickets", json={"service_type": setup["service_id"]}).get_json()
        ticket_id = issued["ticket"]["ticket_id"]
        r = client.post(f"/api/tickets/{ticket_id}/cancel")
        assert r.get_json()["ticket"]["status"] == "cancelled"

    def test_cancel_nonexistent(self, client):
        r = client.post("/api/tickets/ghost/cancel")
        assert r.status_code == 400

    def test_complete_ticket(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        call_r = client.post(f"/api/windows/{setup['window_id']}/call_next",
                             json={"service_type": setup["service_id"]}).get_json()
        ticket_id = call_r["ticket"]["ticket_id"]
        r = client.post(f"/api/tickets/{ticket_id}/complete")
        assert r.get_json()["ticket"]["status"] == "completed"

    def test_miss_ticket(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        call_r = client.post(f"/api/windows/{setup['window_id']}/call_next",
                             json={"service_type": setup["service_id"]}).get_json()
        ticket_id = call_r["ticket"]["ticket_id"]
        r = client.post(f"/api/tickets/{ticket_id}/miss")
        assert r.get_json()["ticket"]["status"] == "missed"

    def test_list_tickets_filter_by_status(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        r = client.get("/api/tickets?status=waiting")
        assert len(r.get_json()["tickets"]) == 1

    def test_list_tickets_filter_invalid_status(self, client):
        r = client.get("/api/tickets?status=invalid")
        assert r.status_code == 400

    def test_ticket_position_in_response(self, client, setup):
        r = client.post("/api/tickets", json={"service_type": setup["service_id"]}).get_json()
        assert "position" in r["ticket"]

    def test_multiple_tickets_numbers_sequential(self, client, setup):
        r1 = client.post("/api/tickets", json={"service_type": setup["service_id"]}).get_json()
        r2 = client.post("/api/tickets", json={"service_type": setup["service_id"]}).get_json()
        assert r2["ticket"]["number"] == r1["ticket"]["number"] + 1


class TestWindowAPI:
    def test_list_windows(self, client, setup):
        r = client.get("/api/windows")
        data = r.get_json()
        assert data["ok"] is True
        assert len(data["windows"]) >= 1

    def test_create_window(self, client, setup):
        r = client.post("/api/windows", json={"name": "Вікно 2", "service_types": [setup["service_id"]]})
        assert r.status_code == 201
        assert r.get_json()["window"]["name"] == "Вікно 2"

    def test_create_window_missing_name(self, client, setup):
        r = client.post("/api/windows", json={"service_types": [setup["service_id"]]})
        assert r.status_code == 400

    def test_open_window(self, client, setup):
        c = get_container()
        w = c.window_service.create_window("В2", [setup["service_id"]])
        r = client.post(f"/api/windows/{w.window_id}/open")
        assert r.get_json()["window"]["status"] == "open"

    def test_close_window(self, client, setup):
        r = client.post(f"/api/windows/{setup['window_id']}/close")
        assert r.get_json()["window"]["status"] == "closed"

    def test_open_nonexistent_window(self, client):
        r = client.post("/api/windows/ghost/open")
        assert r.status_code == 400

    def test_call_next(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        r = client.post(f"/api/windows/{setup['window_id']}/call_next",
                        json={"service_type": setup["service_id"]})
        data = r.get_json()
        assert data["ok"] is True
        assert data["ticket"] is not None

    def test_call_next_empty_queue(self, client, setup):
        r = client.post(f"/api/windows/{setup['window_id']}/call_next",
                        json={"service_type": setup["service_id"]})
        data = r.get_json()
        assert data["ok"] is True
        assert data["ticket"] is None

    def test_call_next_nonexistent_window(self, client, setup):
        r = client.post("/api/windows/ghost/call_next",
                        json={"service_type": setup["service_id"]})
        assert r.status_code == 404


class TestQueueAPI:
    def test_get_queue_empty(self, client):
        r = client.get("/api/queue")
        data = r.get_json()
        assert data["ok"] is True
        assert data["count"] == 0

    def test_get_queue_with_tickets(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        r = client.get("/api/queue")
        assert r.get_json()["count"] == 1

    def test_queue_stats(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        r = client.get("/api/queue/stats")
        stats = r.get_json()["stats"]
        assert stats["waiting"] == 1

    def test_set_strategy_fifo(self, client):
        r = client.post("/api/queue/strategy", json={"strategy": "FIFO"})
        assert r.get_json()["strategy"] == "FIFO"

    def test_set_strategy_priority(self, client):
        r = client.post("/api/queue/strategy", json={"strategy": "PRIORITY"})
        assert r.get_json()["strategy"] == "PRIORITY"

    def test_set_strategy_sjf(self, client):
        r = client.post("/api/queue/strategy", json={"strategy": "SJF"})
        assert r.get_json()["strategy"] == "SJF"

    def test_set_invalid_strategy(self, client):
        r = client.post("/api/queue/strategy", json={"strategy": "INVALID"})
        assert r.status_code == 400


class TestServiceAPI:
    def test_list_services(self, client, setup):
        r = client.get("/api/services")
        assert r.get_json()["ok"] is True

    def test_create_service(self, client):
        r = client.post("/api/services", json={"name": "Нова послуга", "prefix": "N"})
        assert r.status_code == 201
        assert r.get_json()["service"]["name"] == "Нова послуга"

    def test_create_service_missing_name(self, client):
        r = client.post("/api/services", json={"prefix": "N"})
        assert r.status_code == 400


class TestNotificationAPI:
    def test_list_notifications(self, client):
        r = client.get("/api/notifications")
        assert r.get_json()["ok"] is True

    def test_notifications_created_after_ticket(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        r = client.get("/api/notifications")
        assert len(r.get_json()["notifications"]) >= 1

    def test_process_notifications(self, client, setup):
        client.post("/api/tickets", json={"service_type": setup["service_id"]})
        r = client.post("/api/notifications/process")
        assert r.get_json()["processed"] >= 1
