# Domain Model — Модель предметної області

```mermaid
classDiagram
    class Ticket {
        +String ticket_id
        +int number
        +String service_type
        +TicketStatus status
        +TicketPriority priority
        +datetime created_at
        +datetime called_at
        +datetime completed_at
        +String window_id
        +String customer_name
        +String notification_phone
        +int estimated_wait_minutes
        +int position_in_queue
        +to_dict() dict
    }

    class TicketStatus {
        <<enumeration>>
        WAITING
        CALLED
        SERVING
        COMPLETED
        CANCELLED
        MISSED
    }

    class TicketPriority {
        <<enumeration>>
        NORMAL = 1
        PRIORITY = 2
        VIP = 3
    }

    class ServiceWindow {
        +String window_id
        +String name
        +List~String~ service_types
        +WindowStatus status
        +String operator_name
        +String current_ticket_id
        +int tickets_served_today
        +float average_service_minutes
        +can_serve(service_type) bool
        +to_dict() dict
    }

    class WindowStatus {
        <<enumeration>>
        OPEN
        CLOSED
        BREAK
        BUSY
    }

    class ServiceType {
        +String service_id
        +String name
        +String description
        +float avg_duration_minutes
        +String prefix
        +bool is_active
        +to_dict() dict
    }

    class Notification {
        +String notification_id
        +String ticket_id
        +NotificationType notification_type
        +String message
        +datetime created_at
        +bool sent
        +String recipient
        +to_dict() dict
    }

    class NotificationType {
        <<enumeration>>
        TICKET_CREATED
        CALLED_TO_WINDOW
        TURN_SOON
        TICKET_CANCELLED
        TICKET_MISSED
        TICKET_COMPLETED
    }

    Ticket --> TicketStatus : має статус
    Ticket --> TicketPriority : має пріоритет
    Ticket "many" --> "1" ServiceType : відноситься до
    ServiceWindow --> WindowStatus : має статус
    ServiceWindow "1" --> "0..1" Ticket : обслуговує
    ServiceWindow "many" --> "many" ServiceType : обслуговує типи
    Notification --> NotificationType : має тип
    Notification "many" --> "1" Ticket : пов'язана з
```

## Бізнес-правила

- Талон може перейти: `WAITING → CALLED → SERVING → COMPLETED`
- Або: `WAITING/CALLED → CANCELLED`, `CALLED → MISSED`
- Вікно може обслуговувати лише типи послуг зі свого списку `service_types`
- Алгоритм черги (Strategy) визначає порядок видачі талонів
- При кожній зміні статусу талону — Observer надсилає Notification
- `estimated_wait_minutes = кількість_очікуючих × avg_duration_minutes`
