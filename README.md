# Система Електронної Черги

[![CI — Queue System](https://github.com/Vitalik2234/project-2-refactoring/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/Vitalik2234/project-2-refactoring/actions/workflows/ci-pipeline.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Vitalik2234_project-2-refactoring&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Vitalik2234_project-2-refactoring)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=Vitalik2234_project-2-refactoring&metric=coverage)](https://sonarcloud.io/summary/new_code?id=Vitalik2234_project-2-refactoring)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=Vitalik2234_project-2-refactoring&metric=bugs)](https://sonarcloud.io/summary/new_code?id=Vitalik2234_project-2-refactoring)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=Vitalik2234_project-2-refactoring&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=Vitalik2234_project-2-refactoring)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)

Веб-застосунок для керування електронною чергою — талони, вікна, сповіщення, пріоритети.

---

## Зміст

- [Архітектура](#архітектура)
- [GoF Патерни](#gof-патерни)
- [SOLID](#solid)
- [Структура проєкту](#структура-проєкту)
- [Запуск](#запуск)
- [Тести та покриття](#тести-та-покриття)
- [Docker](#docker)
- [API](#api)
- [CI/CD та SonarQube](#cicd-та-sonarqube)
- [UML Діаграми](#uml-діаграми)

---

## Архітектура

**Service-based** з In-Memory сховищем. Код розбитий на чіткі шари:

```
src/models/     — доменні моделі (Ticket, ServiceWindow, ServiceType, Notification)
src/storage/    — інтерфейси (ABC) + In-Memory репозиторії
src/services/   — бізнес-логіка (QueueService, WindowService, ServiceTypeService)
src/utils/      — GoF патерни (Strategy, Observer) та DI-контейнер
tests/          — 250+ тестів (unit + integration)
docs/diagrams/  — UML діаграми
```

**Заборонено:** зовнішні БД, зовнішні API, прямі залежності між шарами. Тільки In-Memory через інтерфейси.

---

## GoF Патерни

### Strategy — алгоритми черги

```python
# Легко замінити алгоритм без зміни QueueService
queue_service.set_strategy(PriorityStrategy())   # VIP → PRIORITY → NORMAL
queue_service.set_strategy(FifoStrategy())        # Перший прийшов — перший обслугований
queue_service.set_strategy(ShortestJobFirstStrategy())  # Найкоротший час послуги — першим
```

| Стратегія | Опис |
|-----------|------|
| `FifoStrategy` | Стандартна черга — за часом надходження |
| `PriorityStrategy` | VIP > PRIORITY > NORMAL, потім за часом |
| `ShortestJobFirstStrategy` | Найменший `estimated_wait_minutes` — першим |

### Observer — сповіщення про події

```python
queue_service.add_observer(NotificationObserver(notification_repo))  # зберігає Notification
queue_service.add_observer(LoggingObserver())                         # аудит-лог подій
```

При кожній події (видача талону, виклик, завершення) — всі спостерігачі отримують сповіщення автоматично.

---

## SOLID

| Принцип | Реалізація |
|---------|------------|
| **S** | `QueueService` — лише логіка черги; репозиторії — лише зберігання |
| **O** | Нова стратегія = новий клас, без зміни `QueueService` |
| **L** | `InMemoryTicketRepository` повністю замінює `ITicketRepository` |
| **I** | Окремі інтерфейси: `ITicketRepository`, `IWindowRepository`, `IQueueStrategy`, `IQueueObserver` |
| **D** | `QueueService(ticket_repo: ITicketRepository)` — залежить від абстракції |

---

## Структура проєкту

```
queue_project/
├── src/
│   ├── models/          # Ticket, ServiceWindow, ServiceType, Notification
│   ├── services/        # QueueService, WindowService, ServiceTypeService
│   ├── storage/         # interfaces.py + in_memory.py
│   └── utils/           # strategies.py, observers.py, container.py
├── tests/
│   ├── unit/            # test_models, test_queue_service, test_repositories,
│   │                    # test_services, test_strategies_observers
│   └── integration/     # test_api, test_queue_flow
├── docs/
│   └── diagrams/        # use_case_diagram.md, domain_model.md, class_diagram.md
├── .cursor/rules/       # architecture.md, testing.md
├── .github/workflows/   # ci-pipeline.yml
├── templates/           # display.html, index.html, kiosk.html
├── .cursorrules         # AI Rules (заборони та вимоги)
├── Dockerfile
├── sonar-project.properties
├── pyproject.toml
└── requirements.txt
```

---

## Запуск

```bash
pip install -r requirements.txt
python app.py
```

Відкрий у браузері:

| URL | Опис |
|-----|------|
| `http://localhost:5000` | Адмін-панель оператора |
| `http://localhost:5000/kiosk` | Кіоск для клієнтів |
| `http://localhost:5000/display` | Публічне табло |

---

## Тести та покриття

```bash
# Запустити всі тести з покриттям
pytest --cov=src --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml -v

# Лише unit-тести
pytest tests/unit/ -v

# Лише integration-тести
pytest tests/integration/ -v
```

Звіти після запуску:

- `reports/coverage_html/index.html` — HTML звіт (відкрий у браузері)
- `reports/coverage.xml` — XML для SonarQube
- `reports/junit.xml` — JUnit XML результати тестів

**Вимога Quality Gate:** покриття ≥ 70%, Bugs = 0, 250+ тестів.

---

## Docker

```bash
docker build -t queue-system .
docker run -p 5000:5000 queue-system
```

---

## API

| Метод | URL | Опис |
|-------|-----|------|
| `POST` | `/api/tickets` | Видати талон |
| `GET` | `/api/tickets` | Список талонів |
| `POST` | `/api/tickets/{id}/cancel` | Скасувати талон |
| `POST` | `/api/tickets/{id}/complete` | Завершити обслуговування |
| `POST` | `/api/tickets/{id}/miss` | Позначити як пропущений |
| `GET` | `/api/windows` | Список вікон |
| `POST` | `/api/windows/{id}/call_next` | Викликати наступного клієнта |
| `GET` | `/api/queue/stats` | Статистика черги |
| `POST` | `/api/queue/strategy` | Змінити алгоритм черги |

---

## CI/CD та SonarQube

### Пайплайн (GitHub Actions)

При кожному `push` до `main`/`develop` або PR автоматично виконується:

1. **Build** — встановлення залежностей
2. **Test & Coverage** — pytest з генерацією `junit.xml` та `coverage.xml`/HTML
3. **Artifacts** — збереження звітів (30 днів) — завантажити: Actions → вибрати run → Artifacts
4. **SonarCloud** — аналіз якості коду, Quality Gate

### Налаштування

1. Додай секрети в GitHub → Settings → Secrets:
   - `SONAR_TOKEN` — токен з [sonarcloud.io](https://sonarcloud.io)
2. Замінити `YOUR_USERNAME` у badges вище на свій GitHub username
3. Замінити `your-org` у `sonar-project.properties` на свою організацію SonarCloud

### Branch Protection (налаштувати вручну)

GitHub → Settings → Branches → Add rule для `main`:
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date
- Обов'язкові checks: `Tests & Coverage`, `SonarCloud Analysis`

---

## UML Діаграми

Всі діаграми у форматі Mermaid (рендеряться у GitHub):

- [`docs/diagrams/use_case_diagram.md`](docs/diagrams/use_case_diagram.md) — Use Case Diagram з акторами та сценаріями
- [`docs/diagrams/domain_model.md`](docs/diagrams/domain_model.md) — Domain Model (всі сутності та зв'язки)
- [`docs/diagrams/class_diagram.md`](docs/diagrams/class_diagram.md) — Class Diagram (патерни, SOLID, шари)
