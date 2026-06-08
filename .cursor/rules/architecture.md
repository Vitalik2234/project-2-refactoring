# Architecture — Electronic Queue System

## Overview

Service-based architecture with strict In-Memory storage. No external databases, no external APIs.

## Layer Structure

```
src/
├── models/       Pure dataclasses — no business logic, no imports from other layers
├── storage/      interfaces.py (ABC) + in_memory.py (implementations)
├── services/     Business logic — depends only on storage interfaces (DIP)
└── utils/        GoF patterns (Strategy, Observer) + DI Container
```

## Rules for AI Code Generation

1. **Every service/repository MUST have an ABC interface** in `storage/interfaces.py` or `utils/`
2. **No direct instantiation** of concrete classes in services — inject via constructor
3. **No external libraries** for storage (no SQLite, Redis, MongoDB, requests to external APIs)
4. **New service?** → Add to `Container` in `src/utils/container.py`
5. **New repository?** → Implement `IXxxRepository` interface first, then `InMemoryXxxRepository`

## GoF Patterns

### Strategy (src/utils/strategies.py)
- Interface: `IQueueStrategy` with `sort(tickets)` and `get_name()`
- Implementations: `FifoStrategy`, `PriorityStrategy`, `ShortestJobFirstStrategy`
- Used in: `QueueService._strategy`
- Switch at runtime: `queue_service.set_strategy(PriorityStrategy())`

### Observer (src/utils/observers.py)
- Interface: `IQueueObserver` with 5 event methods
- Implementations: `NotificationObserver`, `LoggingObserver`
- Register: `queue_service.add_observer(observer)`
- Events: `on_ticket_created`, `on_ticket_called`, `on_ticket_completed`, `on_ticket_cancelled`, `on_ticket_missed`

## Data Flow

```
HTTP Request
    → app.py (Flask route)
    → Container.get_container() (DI)
    → QueueService (business logic)
    → ITicketRepository (abstraction)
    → InMemoryTicketRepository (implementation)
    → [Observer notifications triggered]
    → HTTP Response (JSON)
```

## In-Memory Storage

All repositories use `Dict[str, Entity]` keyed by entity ID:
- `InMemoryTicketRepository._store: Dict[str, Ticket]`
- `InMemoryWindowRepository._store: Dict[str, ServiceWindow]`
- `InMemoryServiceTypeRepository._store: Dict[str, ServiceType]`
- `InMemoryNotificationRepository._store: Dict[str, Notification]`

Data resets on app restart — this is intentional for the academic project.
