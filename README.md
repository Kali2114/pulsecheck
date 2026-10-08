# PulseCheck

An uptime monitoring app, a small [UptimeRobot](https://uptimerobot.com/) /
Statuspage clone. You register the URLs you want to watch. PulseCheck pings each one on
its own schedule, records response times, detects outages and publishes a public status
page that anyone can open without logging in.

> 🚧 **Work in progress.** The checker runs end to end: monitors live in PostgreSQL, a
> scheduler pings them over real HTTP and stores the results. Auth logic is done; the web
> API, dashboard and deployment are next. See the [roadmap](#roadmap).

## Why this project

PulseCheck is meant to go beyond a CRUD app. It includes a scheduler that runs each
monitor on its own interval, outbound HTTP checks with timeouts and retries, an incident
state machine, and live dashboard updates over WebSockets. The target is a real
deployment on AWS, with a public status page as the live demo.

## How it's built

**Domain first, test driven.** The core logic in `app/domain/` is plain Python with no
framework imports. It was written test-first, before any web or database code existed.
`app/infrastructure/` plugs the real world into it.

- **Time is passed in.** The domain never calls `datetime.now()`. The caller passes
  `now`, so tests control time completely; only the scheduler job reads the real clock.
- **The outside world is behind protocols.** The domain depends on small protocols
  (`Pinger`, `PasswordHasher`, the repositories). Tests use fakes; production uses
  `httpx`, a real hasher and PostgreSQL.
- **Repositories are interchangeable.** In-memory repositories back the domain tests;
  SQLAlchemy repositories with the same methods are tested against a real PostgreSQL
  test database, each test inside a transaction that is rolled back.
- **One checker run is one unit of work.** Each scheduled run opens a session, checks
  every due monitor, and commits — or rolls the whole run back if anything fails.

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
- **A monitor is due up to 1 second early.** The scheduler ticks every 10 seconds, and
  ticks drift by fractions of a millisecond. With a 10-second monitor, a tick 0.2 ms
  early used to mean "not due yet", so checks silently ran every 20 seconds. A first real
  run exposed it; a failing test reproduced it; tests now pin the tolerance just inside,
  on, and just outside the boundary.
- **Login doesn't reveal which emails have accounts.** An unknown email and a wrong
  password raise the same error, and both run the (deliberately slow) password check, so
  the response time doesn't give it away either. Emails are trimmed and lowercased on
  both register and login.
- **The scheduler runs inside the app process.** It starts and stops with FastAPI, so the
  app must run as a single process; more workers would check every monitor once each.

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
├── domain/                  # business logic, framework-free
│   ├── monitor.py                    # Monitor + scheduling (is_due)
│   ├── check_result.py               # result of a single check
│   ├── check_service.py              # pings due monitors, retries, stores results
│   ├── pinger.py                     # PingResult + Pinger protocol
│   ├── statistics.py                 # uptime %, average response time
│   ├── user.py                       # User
│   ├── auth_service.py               # register, login
│   ├── password_hasher.py            # PasswordHasher protocol
│   ├── *_repository.py               # repository protocols + in-memory versions
│   └── exceptions.py
├── infrastructure/          # the real world
│   ├── database.py, models.py        # SQLAlchemy engine, session, table models
│   ├── *_repository.py               # PostgreSQL repositories
│   ├── http_pinger.py                # Pinger over httpx
│   ├── check_runner.py               # one checker run = one transaction
│   └── scheduler.py, scheduler_runner.py  # APScheduler job, start/stop
├── api/                     # FastAPI routes (next)
├── main.py                  # FastAPI app; starts/stops the scheduler
└── config.py                # settings from environment
alembic/                     # database migrations
tests/
├── domain/                  # unit tests, no I/O
├── infrastructure/          # integration tests against real PostgreSQL
└── api/                     # app tests
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

# start the app (and the checker) — a single process, see below
uvicorn app.main:app
```

The app starts a background scheduler that checks due monitors every 10 seconds. Run it
as **one** process (no `--workers`), or each process checks every monitor. Set
`SCHEDULER_ENABLED=false` to start the app without it.

## Tests

```bash
pytest
```

Runs all 128 tests with a coverage report (100%). The integration tests use the test
database, so start PostgreSQL first (`docker compose up -d`). Tests never start the real
scheduler.

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
- [x] Persistence: SQLAlchemy models, Alembic migrations, database repositories
- [x] Real HTTP checker (httpx) and scheduler (APScheduler)
- [x] Auth domain logic: register and log in
- [ ] Auth: users in PostgreSQL, JWT, API endpoints
- [ ] Monitor CRUD API
- [ ] Dashboard with response-time chart

**Later**
- [ ] Incident detection: N consecutive failures open an incident, recovery closes it
- [ ] Notifications: email, then webhooks
- [ ] Live updates over WebSockets
- [ ] Public status page, no login needed
- [ ] Demo account, reset automatically
- [ ] Deployment on AWS

## How this was built

I wrote the domain and backend logic myself, test-first. I use
[Claude Code](https://claude.com/claude-code) as a mentor and reviewer: when I ask for a
review, it points at problems and gives hints rather than solutions, and I write the fixes.
On request it has also written some tests, setup and wiring code and documentation like
this README. Every commit it contributed to is marked `Co-Authored-By: Claude` in the
history.

## License

[GPL-3.0](LICENSE)
