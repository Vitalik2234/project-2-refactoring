from flask import Flask, render_template, request, jsonify, redirect, url_for
from src.utils.container import get_container, reset_container
from src.models import TicketPriority
from src.utils.strategies import FifoStrategy, PriorityStrategy, ShortestJobFirstStrategy

app = Flask(__name__)


def _container():
    return get_container()


# ─── Pages ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    c = _container()
    stats = c.queue_service.get_queue_stats()
    windows = c.window_service.get_all_windows()
    services = c.service_type_service.get_active()
    queue = c.queue_service.get_queue()
    notifications = c.notification_service.get_all()
    return render_template(
        "index.html",
        stats=stats,
        windows=[w.to_dict() for w in windows],
        services=[s.to_dict() for s in services],
        queue=[t.to_dict() for t in queue],
        notifications=[n.to_dict() for n in reversed(notifications[-20:])],
        strategy=c.queue_service.get_strategy_name(),
    )


@app.route("/kiosk")
def kiosk():
    c = _container()
    services = c.service_type_service.get_active()
    return render_template("kiosk.html", services=[s.to_dict() for s in services])


@app.route("/display")
def display():
    c = _container()
    called = c.ticket_repo.find_by_status(__import__('src.models', fromlist=['TicketStatus']).TicketStatus.CALLED)
    serving = c.ticket_repo.find_by_status(__import__('src.models', fromlist=['TicketStatus']).TicketStatus.SERVING)
    return render_template(
        "display.html",
        called=[t.to_dict() for t in called],
        serving=[t.to_dict() for t in serving],
    )


# ─── API: Tickets ──────────────────────────────────────────────────────────────

@app.route("/api/tickets", methods=["POST"])
def issue_ticket():
    data = request.get_json(force=True)
    service_type = data.get("service_type")
    customer_name = data.get("customer_name")
    phone = data.get("notification_phone")
    priority_val = data.get("priority", 1)
    try:
        priority = TicketPriority(priority_val)
        ticket = _container().queue_service.issue_ticket(service_type, customer_name, phone, priority)
        pos, wait = _container().queue_service.get_position(ticket.ticket_id)
        result = ticket.to_dict()
        result["position"] = pos
        result["estimated_wait_minutes"] = wait
        return jsonify({"ok": True, "ticket": result}), 201
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/tickets", methods=["GET"])
def list_tickets():
    c = _container()
    status_filter = request.args.get("status")
    service_filter = request.args.get("service_type")
    if status_filter:
        from src.models import TicketStatus
        try:
            status = TicketStatus(status_filter)
            tickets = c.ticket_repo.find_by_status(status)
        except ValueError:
            return jsonify({"ok": False, "error": "Invalid status"}), 400
    elif service_filter:
        tickets = c.ticket_repo.find_by_service_type(service_filter)
    else:
        tickets = c.ticket_repo.find_all()
    return jsonify({"ok": True, "tickets": [t.to_dict() for t in tickets]})


@app.route("/api/tickets/<ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    ticket = _container().ticket_repo.find_by_id(ticket_id)
    if not ticket:
        return jsonify({"ok": False, "error": "Ticket not found"}), 404
    pos, wait = _container().queue_service.get_position(ticket_id)
    result = ticket.to_dict()
    result["position"] = pos
    result["estimated_wait_minutes"] = wait
    return jsonify({"ok": True, "ticket": result})


@app.route("/api/tickets/<ticket_id>/cancel", methods=["POST"])
def cancel_ticket(ticket_id):
    try:
        ticket = _container().queue_service.cancel_ticket(ticket_id)
        return jsonify({"ok": True, "ticket": ticket.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/tickets/<ticket_id>/complete", methods=["POST"])
def complete_ticket(ticket_id):
    c = _container()
    try:
        ticket = c.queue_service.complete_ticket(ticket_id)
        if ticket.window_id:
            try:
                c.window_service.free_window(ticket.window_id)
            except ValueError:
                pass
        return jsonify({"ok": True, "ticket": ticket.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/tickets/<ticket_id>/miss", methods=["POST"])
def miss_ticket(ticket_id):
    c = _container()
    try:
        ticket = c.queue_service.mark_missed(ticket_id)
        if ticket.window_id:
            try:
                c.window_service.free_window(ticket.window_id)
            except ValueError:
                pass
        return jsonify({"ok": True, "ticket": ticket.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ─── API: Windows ──────────────────────────────────────────────────────────────

@app.route("/api/windows", methods=["GET"])
def list_windows():
    windows = _container().window_service.get_all_windows()
    return jsonify({"ok": True, "windows": [w.to_dict() for w in windows]})


@app.route("/api/windows", methods=["POST"])
def create_window():
    data = request.get_json(force=True)
    try:
        w = _container().window_service.create_window(
            data["name"], data["service_types"], data.get("operator_name")
        )
        return jsonify({"ok": True, "window": w.to_dict()}), 201
    except (ValueError, KeyError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/windows/<window_id>/open", methods=["POST"])
def open_window(window_id):
    try:
        w = _container().window_service.open_window(window_id)
        return jsonify({"ok": True, "window": w.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/windows/<window_id>/close", methods=["POST"])
def close_window(window_id):
    try:
        w = _container().window_service.close_window(window_id)
        return jsonify({"ok": True, "window": w.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/windows/<window_id>/call_next", methods=["POST"])
def call_next(window_id):
    c = _container()
    data = request.get_json(force=True)
    service_type = data.get("service_type")
    window = c.window_service.get_window(window_id)
    if not window:
        return jsonify({"ok": False, "error": "Window not found"}), 404
    try:
        ticket = c.queue_service.call_next(service_type, window_id, window.name)
        if ticket:
            c.window_service.assign_ticket(window_id, ticket.ticket_id)
            return jsonify({"ok": True, "ticket": ticket.to_dict()})
        return jsonify({"ok": True, "ticket": None, "message": "Queue is empty"})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ─── API: Services ─────────────────────────────────────────────────────────────

@app.route("/api/services", methods=["GET"])
def list_services():
    services = _container().service_type_service.get_all()
    return jsonify({"ok": True, "services": [s.to_dict() for s in services]})


@app.route("/api/services", methods=["POST"])
def create_service():
    data = request.get_json(force=True)
    try:
        s = _container().service_type_service.create_service(
            data["name"],
            data.get("description", ""),
            float(data.get("avg_duration_minutes", 5.0)),
            data.get("prefix", "A"),
        )
        return jsonify({"ok": True, "service": s.to_dict()}), 201
    except (ValueError, KeyError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ─── API: Queue ────────────────────────────────────────────────────────────────

@app.route("/api/queue", methods=["GET"])
def get_queue():
    service_type = request.args.get("service_type")
    queue = _container().queue_service.get_queue(service_type)
    return jsonify({"ok": True, "queue": [t.to_dict() for t in queue], "count": len(queue)})


@app.route("/api/queue/stats", methods=["GET"])
def queue_stats():
    stats = _container().queue_service.get_queue_stats()
    return jsonify({"ok": True, "stats": stats})


@app.route("/api/queue/strategy", methods=["POST"])
def set_strategy():
    data = request.get_json(force=True)
    strategies = {"FIFO": FifoStrategy(), "PRIORITY": PriorityStrategy(), "SJF": ShortestJobFirstStrategy()}
    name = data.get("strategy", "FIFO").upper()
    if name not in strategies:
        return jsonify({"ok": False, "error": f"Unknown strategy: {name}"}), 400
    _container().queue_service.set_strategy(strategies[name])
    return jsonify({"ok": True, "strategy": name})


# ─── API: Notifications ────────────────────────────────────────────────────────

@app.route("/api/notifications", methods=["GET"])
def list_notifications():
    notifications = _container().notification_service.get_all()
    return jsonify({"ok": True, "notifications": [n.to_dict() for n in reversed(notifications)]})


@app.route("/api/notifications/process", methods=["POST"])
def process_notifications():
    count = _container().notification_service.process_pending()
    return jsonify({"ok": True, "processed": count})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
