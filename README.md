# PulseCheck

An uptime monitoring app, a small [UptimeRobot](https://uptimerobot.com/) /
Statuspage clone. You register the URLs you want to watch. PulseCheck pings each one on
its own schedule, records response times, detects outages and publishes a public status
page that anyone can open without logging in.

> 🚧 **Work in progress.** The v1 core works end to end: you sign up, add monitors in the
> dashboard, a scheduler pings them over real HTTP, and the dashboard shows live status,
> uptime and a response-time chart. Deployment to AWS is next, then incident detection.
> See the [roadmap](#roadmap).

## Features

- **Accounts:** register and log in; passwords hashed with bcrypt, sessions as JWTs.
- **Monitors:** add, edit and delete the URLs you watch, each with its own check
  interval (10 seconds to 24 hours), timeout and number of attempts.
- **Checker:** a background scheduler pings every due monitor, retries failures, and
  stores the result and response time of each check.
- **Dashboard:** every monitor's current status at a glance, refreshed automatically.
- **Monitor page:** uptime, average response time and a response-time chart over the
  last hour, day or week, with failed checks marked in red.

## Why this project

PulseCheck is meant to go beyond a CRUD app. It includes a scheduler that runs each
monitor on its own interval, outbound HTTP checks with timeouts and retries, an incident
state machine, and live dashboard updates over WebSockets. The target is a real
deployment on AWS, with a public status page as the live demo.

## How it's built

**Domain first, test driven.** The core logic in `app/domain/` is plain Python with no
framework imports. It was written test-first, before any web or database code existed.
`app/infrastructure/` plugs the real world into it, and `app/api/` exposes it over HTTP.

- **Time is passed in.** The domain never calls `datetime.now()`. The caller passes
  `now`, so tests control time completely; only the scheduler job and one API dependency
  read the real clock.
- **The outside world is behind protocols.** The domain depends on small protocols
  (`Pinger`, `PasswordHasher`, the repositories). Tests use fakes; production uses
  `httpx`, bcrypt and PostgreSQL.
- **Repositories are interchangeable.** In-memory repositories back the domain tests;
  SQLAlchemy repositories with the same methods are tested against a real PostgreSQL
  test database, each test inside a transaction that is rolled back.
- **One unit of work per run and per request.** Each scheduled checker run, and each API
  request, gets its own database session: it commits on success and rolls everything
  back on any error.
- **Tests are checked, not just green.** 100% line coverage is required for every
  commit, and new tests are mutation-checked: break the code a test claims to protect
  and make sure the test actually fails.

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
- **No rounding in the domain or the API.** Statistics return full precision. Rounding is
  decided where the numbers are displayed.
- **A monitor is due up to 1 second early.** The scheduler ticks every 10 seconds, and
  ticks drift by fractions of a millisecond. With a 10-second monitor, a tick 0.2 ms
  early used to mean "not due yet", so checks silently ran every 20 seconds. A first real
  run exposed it; a failing test reproduced it; tests now pin the tolerance just inside,
  on, and just outside the boundary.
- **Login doesn't reveal which emails have accounts.** An unknown email and a wrong
  password raise the same error, and both run the (deliberately slow) password check, so
  the response time doesn't give it away either. Emails are trimmed and lowercased on
  both register and login.
- **Someone else's monitor looks exactly like a missing one.** Every monitor route
  answers `404` with the same message for "doesn't exist" and "not yours", so ids can't
  be probed to find other users' monitors.
- **The monitor list loads every status in one query.** Each monitor carries its latest
  check (`latest_check`, or `null` before the first one), fetched for the whole list with
  a single PostgreSQL `DISTINCT ON` query instead of one query per monitor. It's a fact
  ("what the last check saw"), not an "up/down" flag, so incident detection can define
  "down" later without changing what the field means.
- **History requests are capped.** Check results and statistics cover the last hour by
  default and at most 7 days; older requests are rejected rather than silently cut.
- **The chart never hides an outage.** Over long ranges the chart averages checks into
  time buckets, and any bucket with even one failed check gets a red marker. Chart.js's
  built-in decimation was ruled out because it can drop single failed points.
- **The scheduler runs inside the app process.** It starts and stops with FastAPI, so the
  app must run as a single process; more workers would check every monitor once each.

## API

Interactive docs are at `/docs` once the app is running. Every `/monitors` route needs a
bearer token and only ever sees the current user's monitors.

| Method | Path | |
| --- | --- | --- |
| `POST` | `/auth/register` | create an account |
| `POST` | `/auth/login` | log in (form data), returns a JWT |
| `GET` | `/auth/me` | the current user |
| `GET` / `POST` | `/monitors` | list your monitors (with their latest check) / add one |
| `GET` / `PATCH` / `DELETE` | `/monitors/{id}` | read, partly update or delete a monitor |
| `GET` | `/monitors/{id}/check-results?since=` | check history, oldest first |
| `GET` | `/monitors/{id}/stats?since=` | uptime %, average response time, check count |

## Tech stack

| Layer | Technology |
| --- | --- |
| Domain | Python 3.12 (stdlib only) |
| Web / API | FastAPI, Pydantic |
| Frontend | HTML, CSS and native ES modules (no framework, no build step), Chart.js |
| Persistence | PostgreSQL, SQLAlchemy 2, Alembic, psycopg 3 |
| Checker | APScheduler, httpx |
| Auth | JWT (PyJWT), bcrypt |
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
│   ├── password_hasher.py            # bcrypt
│   ├── jwt_token_service.py          # create / decode access tokens
│   ├── check_runner.py               # one checker run = one transaction
│   └── scheduler.py, scheduler_runner.py  # APScheduler job, start/stop
├── api/                     # FastAPI routes, schemas, dependencies
├── static/                  # the dashboard: index.html, CSS, ES modules
├── main.py                  # FastAPI app, error handlers; starts/stops the scheduler
└── config.py                # settings from environment
alembic/                     # database migrations
tests/
├── domain/                  # unit tests, no I/O
├── infrastructure/          # integration tests against real PostgreSQL
└── api/                     # HTTP tests through FastAPI's TestClient
```

## Running locally

Requirements: Python 3.12 and Docker.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# settings: copy the sample and fill in your values
cp .env.sample .env
# SECRET_KEY must be at least 32 bytes — generate one with:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# PostgreSQL (development and test databases)
docker compose up -d

# create the tables
alembic upgrade head

# start the app (and the checker) — a single process, see below
uvicorn app.main:app
```

Open <http://localhost:8000>, create an account and add a monitor. The API docs are at
<http://localhost:8000/docs>.

The app starts a background scheduler that checks due monitors every 10 seconds. Run it
as **one** process (no `--workers`), or each process checks every monitor. Set
`SCHEDULER_ENABLED=false` to start the app without it.

## Tests

```bash
pytest
```

Runs all 257 tests with a coverage report (100%). The integration and API tests use the
test database, so start PostgreSQL first (`docker compose up -d`). Tests never start the
real scheduler. GitHub Actions runs the suite against a PostgreSQL service on every push and pull request
to `main`.

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
- [x] Auth: register, log in, JWT, users in PostgreSQL
- [x] Monitor CRUD API, scoped per user
- [x] Check history and statistics API
- [x] Dashboard: monitor list, monitor page with response-time chart, add / edit / delete
- [ ] Deployment on AWS

**Later**
- [ ] Incident detection: N consecutive failures open an incident, recovery closes it
- [ ] Notifications: email, then webhooks
- [ ] Live updates over WebSockets
- [ ] Public status page, no login needed
- [ ] Demo account, reset automatically

## How this was built

I wrote the domain and backend logic myself, test-first. I use
[Claude Code](https://claude.com/claude-code) as a mentor and reviewer: when I ask for a
review, it points at problems and gives hints rather than solutions, and I write the fixes.
On request it has also written some tests, setup and wiring code and documentation like
this README.

The dashboard frontend (HTML, CSS and JavaScript in `app/static/`) is the exception:
Claude Code wrote it, and I directed it — deciding what it should do and reviewing each
step in the browser. Every commit Claude contributed to is marked
`Co-Authored-By: Claude` in the history.

## License

[GPL-3.0](LICENSE)
