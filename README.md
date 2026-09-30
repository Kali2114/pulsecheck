# PulseCheck

An uptime monitoring app, a small [UptimeRobot](https://uptimerobot.com/) /
Statuspage clone. You register the URLs you want to watch. PulseCheck pings each one on
its own schedule, records response times, detects outages and publishes a public status
page that anyone can open without logging in.

> 🚧 **Work in progress.** The core domain logic is done and fully tested. Persistence,
> the web API and deployment are next. See the [roadmap](#roadmap).

## Why this project

PulseCheck is meant to go beyond a CRUD app. It includes a scheduler that runs each
monitor on its own interval, outbound HTTP checks with timeouts and retries, an incident
state machine, and live dashboard updates over WebSockets. The target is a real
deployment on AWS, with a public status page as the live demo.

## How it's built

**Domain first, test driven.** The core logic in `app/domain/` is plain Python with no
framework imports. It was written test-first, before any web or database code exists.

- **Time is passed in.** The checker never calls `datetime.now()`. The caller passes
  `now`, so tests control time completely.
- **The network is behind an interface.** The checker depends on a small `Pinger`
  protocol, so tests use a fake instead of real HTTP calls. The real `httpx`
  implementation plugs in later.
- **Repositories are interchangeable.** The domain uses in-memory repositories. PostgreSQL
  repositories with the same methods come next.

### Design decisions

- **What counts as "up":** a 2xx or 3xx response. A timeout or connection error is down.
- **Response time of a failed check:**
  - a *timeout* has no response time, so it's stored as empty, not `0`. A `0` would make
    a dead site look like the fastest one.
  - an *HTTP 500 in 80 ms* did get a response, so the time is real and is kept.
- **Average response time counts only successful checks.** Errors are often fast, and a
  metric shouldn't look better exactly when the site is broken.
- **Retries:** a failed ping is retried up to the monitor's limit, stopping at the first
  success. Each check stores **one** result, not one per attempt.
- **No rounding in the domain.** Statistics return full precision. Rounding is decided
  where the numbers are displayed.

## Tech stack

| Layer | Technology |
| --- | --- |
| Domain | Python 3.12 (stdlib only) |
| Web / API | FastAPI, WebSockets |
| Persistence | PostgreSQL, SQLAlchemy 2, Alembic, psycopg 3 |
| Checker | APScheduler, httpx |
| Auth | JWT, bcrypt |
| Tooling | pytest, pytest-cov, Ruff, Black, pre-commit, GitHub Actions |
| Deployment | Docker, AWS (planned) |

## Project structure

```
app/
├── domain/           # business logic, framework-free, fully tested
│   ├── monitor.py                    # Monitor + scheduling (is_due)
│   ├── check_result.py               # result of a single check
│   ├── check_service.py              # pings due monitors, retries, stores results
│   ├── pinger.py                     # PingResult + Pinger protocol
│   ├── statistics.py                 # uptime %, average response time
│   ├── monitor_repository.py         # in-memory repositories
│   └── check_result_repository.py
├── infrastructure/   # database, real HTTP client (in progress)
├── api/              # FastAPI routes (planned)
└── config.py         # settings from environment
tests/
└── domain/           # unit tests for app/domain
```

## Running locally

Requirements: Python 3.12 and Docker.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# settings: copy the sample and fill in your values
cp .env.sample .env

# PostgreSQL (development and test databases)
docker compose up -d

# create the tables
alembic upgrade head
```

## Tests

```bash
pytest
```

Runs the test suite with a coverage report. The domain layer has 100% coverage.

Code style is enforced with Ruff and Black through pre-commit:

```bash
pre-commit install
pre-commit run --all-files
```

## Roadmap

**v1: a demoable core**
- [x] Domain: monitors, per-monitor scheduling, check results
- [x] Checker service with retries and timeout handling
- [x] Uptime and response-time statistics
- [x] Local PostgreSQL with Docker Compose
- [ ] Persistence: SQLAlchemy models, Alembic migrations, database repositories
- [ ] Real HTTP checker (httpx) and scheduler (APScheduler)
- [ ] Auth: register and log in with JWT
- [ ] Monitor CRUD API
- [ ] Dashboard with response-time chart

**Later**
- [ ] Incident detection: N consecutive failures open an incident, recovery closes it
- [ ] Notifications: email, then webhooks
- [ ] Live updates over WebSockets
- [ ] Public status page, no login needed
- [ ] Demo account, reset automatically
- [ ] Deployment on AWS

## License

[GPL-3.0](LICENSE)
