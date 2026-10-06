# pulsecheck — "PulseCheck"

Uptime/status monitoring app — a small UptimeRobot/Statuspage clone. You register endpoints to
watch; the app pings them on a configurable schedule, tracks response times, detects incidents
(consecutive failures → down, recovery → resolved), notifies you, and publishes a public status
page nobody needs to log in to see.

Portfolio piece — built deliberately more technically ambitious than a CRUD app (real-time
WebSocket push, an incident state machine, outbound HTTP monitoring) and meant to actually deploy
(target: AWS) with a recruiter-facing demo: a public status page (no login) plus a seeded demo
account for the authenticated dashboard.

## Why this project (context for future sessions)

Built right after [[wtf-project-scope]] (fridgewatch / "What The Fridge?", a fridge inventory
tracker) reached a natural stopping point. The user wanted something with more algorithmic/technical
depth than fridgewatch's CRUD-plus-one-feature shape, that solves a recognizable real problem, and
that deploys somewhere real (AWS) for a CV. Sibling project, same user, same workflow preferences —
see [[coaching-mode]] and [[tdd-domain-first-workflow]], both still apply here.

## Stack

FastAPI, uvicorn, pytest, httpx (TestClient **and** as the runtime HTTP client the checker uses to
ping monitored URLs — new: fridgewatch never made outbound HTTP calls from its own code), SQLAlchemy
+ Alembic (set up from day one this time — fridgewatch retrofitted Alembic after already hitting a
schema-drift bug; don't repeat that), APScheduler (in-process, started from the FastAPI lifespan —
so run a single process).
No JS framework for the frontend, matching fridgewatch's choice — but this project needs actual
WebSocket client JS for live updates, which fridgewatch's frontend never needed.

**Database: Postgres (decided 2026-09-29).** SQLite would have worked at demo scale (~14k
ping rows/day for 10 monitors at 1/min is fine for it), so volume wasn't the deciding factor.
Postgres won on: data living outside the app container (redeploys can't wipe it), the scheduler
and API writing concurrently, time-series queries in SQL (`date_trunc` for chart buckets,
`percentile_cont` for p95), and CV relevance. Driver is psycopg 3 (`postgresql+psycopg://`).
Local dev runs Postgres in Docker (docker-compose); RDS vs. Postgres-in-Docker-on-EC2 is still
open and belongs to the deployment decision — code is identical either way, only `DATABASE_URL`
changes.

Persistence design:
- SQLAlchemy table models live in `app/infrastructure/`, **separate** from the domain classes;
  repositories map between them. The domain never imports SQLAlchemy.
- DB repositories expose the same methods as the in-memory ones so `CheckService` works with
  either. Domain tests keep using the in-memory repos; DB repos get integration tests against a
  real Postgres test database (per-test transaction rollback). Don't test them against SQLite —
  it hides Postgres-specific behaviour.
- `monitors.user_id` gets its FK to `users` in a later migration, when auth lands.
- Check results grow unbounded — plan a retention/cleanup job eventually.

## Workflow rules (same as fridgewatch, carried over deliberately)

- **TDD, domain-first.** Pure Python classes + tests before any web/FastAPI layer.
- Domain logic stays free of framework imports; clocks/time are always injected, never
  `datetime.now()` inline. The incident-detection state machine and the response-time/uptime-
  percentage calculations belong here — they're the parts with real logic worth testing.
- When the user says **"check"**, they want a code review (hints/pointers, not a rewritten
  solution — they're practicing solo coding and want to write the fix themselves).
- Commit and push in small increments, only when the user explicitly asks.
- The user is **not confident writing frontend code** — for frontend/CSS/visual work, default to
  building it yourself with the user directing by screenshot/description, rather than coaching them
  to write it. This is the opposite default from backend/domain work, where they write and you review.

## v1 scope (ship a demoable core first)

- Auth: register/login, hashed passwords, JWT (same pattern as fridgewatch — this part should go
  fast)
- Monitor CRUD: url, check interval, timeout, retry count — scoped per user
- Scheduled checker: pings each monitor per its own interval (not one global interval — this is
  more involved than fridgewatch's single daily job), records response time + up/down result
- Dashboard: list of monitors, current status, response-time history (a simple chart)

## Later milestones (do not start until v1 is deployable; each shippable on its own)

1. **Incident detection** — a state machine: N consecutive failures → incident opens; recovery →
   incident closes, duration tracked. Real domain-logic substance, good TDD material — don't rush
   past this one into the web layer.
2. **Notifications** — email first (you already have working `smtplib` code in fridgewatch's
   `app/notifications.py` to reference), webhook later.
3. **Live WebSocket updates** — push status/incident changes to connected dashboard clients as
   they happen. Genuinely new territory vs. fridgewatch's plain request/response REST API.
4. **Public status page** — unauthenticated route; monitors get a `public: bool` flag; this is the
   zero-friction "recruiter clicks a link and sees it working" surface — prioritize this over the
   demo account once the core works, since it needs no credentials at all.
5. **Demo account seeding** — a known login for the full authenticated dashboard experience,
   documented in the README. Since it's a public login, it needs a scheduled job resetting it back
   to seed state periodically (e.g. hourly) so it doesn't accumulate junk/abuse — same APScheduler
   pattern as the reminder job and the checker itself.

## Deployment target

AWS. Not decided yet: EC2 vs. ECS/Fargate vs. Elastic Beanstalk — check free-tier eligibility
(750 hrs/month of a t2/t3.micro under the 12-month free tier, if not already used) before assuming
cost. Fly.io has no free tier as of late 2024; Render's free tier blocks outbound SMTP ports and
has no persistent disk on the free plan — neither is a good fit for this app's notification/DB
needs even at demo scale, which is part of why AWS was chosen over them this time.

## Current status (2026-10-06)

**Domain layer for v1 is done** (`app/domain/`, 100% test coverage, all pushed to `main`):
- `Monitor` — `is_due(now)`; validates `retry_count >= 1`. Note: `retry_count` means *total
  attempts* (1 = one ping, no retries), despite the name — a rename to `max_attempts` was
  considered but not done.
- `CheckResult` — `response_time_ms` is `None` when no response was received (timeout /
  connection error). A down result *with* a response (e.g. HTTP 500) keeps its time.
- `InMemoryMonitorRepository`, `InMemoryCheckResultRepository` (`list_for_monitor(monitor_id,
  since=None)` oldest-first, `get_latest`).
- `statistics.py` — `uptime_percentage`, `average_response_time` (up checks only; no rounding in
  the domain — rounding is a display concern).
- `PingResult` + `Pinger` Protocol (`app/domain/pinger.py`, `@runtime_checkable`) — `is_up()`
  is 2xx/3xx; no status code = down.
- `CheckService.check(now)` — pings due monitors with retries (stops at first up), stores one
  result per check, updates `last_checked_at` via `update_monitor`.

Updates go through `Monitor.with_changes(payload)`: only `Monitor.EDITABLE_FIELDS` (id and
user_id are fixed; unknown keys raise `InvalidMonitorUpdate`), returns a new validated Monitor.
Both repositories' `update_monitor` use it and validate *before* storing anything.
Repository interfaces are Protocols in the domain (`MonitorRepository`, `CheckResultRepository`,
`@runtime_checkable`); `CheckService` depends on those, never on a concrete repository. Each
implementation has a test asserting `isinstance(repo, Protocol)` — note that only checks method
*names* exist, not signatures (no mypy in the project yet).

**Persistence layer is done** (all pushed to `main`):
- Done: `docker-compose.yml` (Postgres 17, named volume, healthcheck; init script
  `docker/postgres/init-test-db.sh` creates the test DB from `POSTGRES_TEST_DB`). Local port is
  set in `.env` (the user's is 5434). `app/config.py` — `Settings` (pydantic-settings, reads
  `.env`, `extra="ignore"`), `database_url` / `test_database_url` built with SQLAlchemy
  `URL.create` so passwords are escaped. **Gotcha:** `str(url)` masks the password as `***` —
  anywhere a string is needed (Alembic config), use `url.render_as_string(hide_password=False)`.
  CI sets fake `POSTGRES_*` env vars because `settings = Settings()` runs at import time.
- Done: `app/infrastructure/database.py` (`Base`, `engine`, `SessionLocal` with
  `expire_on_commit=False`), `models.py` (`MonitorModel`, table `monitors`). Alembic set up;
  first migration creates `monitors`. `alembic/env.py` takes the URL from `settings` — or from
  `config.attributes["database_url"]` (a `URL`), which is how tests should target the test DB.
  Never put the URL through `alembic.ini` / `set_main_option`: configparser chokes on the `%`
  in escaped passwords. Post-write hooks run ruff + black on new migrations.
- **All datetimes are UTC-aware** (DB columns are `timestamptz`; naive vs aware can't be
  compared). Tests use `tzinfo=UTC`; the scheduler must pass `datetime.now(UTC)`.
- Done: `SQLAlchemyMonitorRepository` (all six methods) with integration tests in
  `tests/infrastructure/` — `conftest.py` migrates the test DB once per session and gives each
  test a session joined to an outer transaction (`join_transaction_mode="create_savepoint"`)
  that's rolled back. Tests call `db_session.expire_all()` before re-reading to prove data
  really hit Postgres (`session.get` otherwise serves the identity-map cache). Listings order by
  id. CI runs a `postgres:17` service container. Models use `MappedAsDataclass` (typed
  `__init__`; `id` is `init=False`).
- Done: `CheckResultModel` (table `check_results`, FK to `monitors` with `ON DELETE CASCADE`,
  index on `(monitor_id, checked_at)`) + migration, and `SQLAlchemyCheckResultRepository`
  (`add_check_result`, `list_for_monitor`, `get_latest`). Filtering, ordering and `LIMIT 1` all
  happen in SQL — note SQLAlchemy 2.0's `Result.first()` does **not** add a `LIMIT`, so keep
  `.limit(1)` in the statement. Ordering tests insert rows in the *opposite* order to the
  expected output, and filter tests give the other monitor the row that would win without the
  `WHERE`, so a missing clause actually fails.

**HTTP pinger is done** (pushed to `main`):
- `HttpPinger` (`app/infrastructure/http_pinger.py`) takes an injected `httpx.Client`; timeout is
  per request (each monitor has its own). Follows redirects and reports the final status (time
  includes all hops). Catches `httpx.RequestError` (timeouts, connection errors, unsupported
  scheme, too many redirects) **and** `httpx.InvalidURL`, which is *not* a `RequestError` — both
  give a `PingResult` with no status and no time. The full body is downloaded, so response time
  includes it (accepted for now). `int()` truncates the ms.
- Tests (`tests/infrastructure/test_http_pinger.py`) use a `make_pinger(handler)` factory fixture
  over `httpx.MockTransport` that closes its clients. Gotchas learned: a handler must `raise`
  httpx exceptions (returning one gives a misleading "async handler" `TypeError`); a mock
  transport skips the real transport's checks too, so an "invalid URL" test must use a URL httpx
  rejects while *building* the request (e.g. unclosed IPv6 bracket `http://[::1`) — `://bad-url`
  parses as a relative URL instead. Each test was mutation-checked (removing the fix turns it red).

**Check runner is done** (pushed to `main`):
- `run_check(session_factory, pinger, now)` (`app/infrastructure/check_runner.py`) is one checker
  run as a unit of work: fresh session from the factory → both SQLAlchemy repos on it →
  `CheckService.check(now)` → commit; on any exception roll back and **re-raise** (the scheduler
  should see failures); always close. One transaction per run, so one failing ping discards the
  whole run's results — per-monitor commits are a possible later change.
- Test fixtures: `session_factory` (in `tests/infrastructure/conftest.py`) yields a
  `sessionmaker` bound to one connection inside an outer transaction with
  `join_transaction_mode="create_savepoint"` — code under test can `commit()` (only releases a
  savepoint), later sessions see the data, and teardown rolls everything back. `db_session` is
  built on it (one session from the factory).
- Fakes: shared `tests/helpers/fake_pinger.py::FakePinger(result, failing_urls=...)` (fixed
  result, raises `RuntimeError` for chosen URLs); the domain test's `SequencePinger` replays a
  list of results and records calls (for retry tests) — kept separate on purpose.
- The rollback test needs **two** monitors (good one checked first, by id order, then the bad one
  raises) — with one monitor nothing is written before the failure, so it proves nothing. The
  meaningful mutation is turning the `rollback()` into a `commit()` (goes red); a stray commit in
  `finally` does not, because the rollback already ran and `close()` discards uncommitted work.
**Scheduler is wired** (pushed to `main`):
- `create_scheduler(session_factory, pinger, interval_seconds=CHECK_INTERVAL_SECONDS)`
  (`app/infrastructure/scheduler.py`, default 10s) — one global `BackgroundScheduler` interval
  job, `max_instances=1`, `coalesce=True` (3.x defaults, set explicitly to document intent); the job
  reads `datetime.now(UTC)` on every run and calls `run_check`. APScheduler catches and logs job
  exceptions, so a failed run doesn't stop the scheduler.
- `scheduler_runner.py`: `start_scheduler()` builds one `httpx.Client` + `HttpPinger` +
  `SessionLocal` and starts it; `stop_scheduler()` shuts the scheduler down (waits for a running
  job) *then* closes the client. Called from the FastAPI `lifespan` in `app/main.py` (cleanup in
  `try/finally`), only when `settings.scheduler_enabled` (env `SCHEDULER_ENABLED`, default true).
- **In-process means one process only** — with several uvicorn workers every monitor is checked
  once per worker. Run a single process; a separate worker process is the fix if that ever changes.
- `tests/conftest.py` sets `SCHEDULER_ENABLED=false` before `app.config` is imported (settings are
  read at import time), so `TestClient(app)` never starts a real scheduler against the dev DB.
  `tests/api/test_lifespan.py` checks both branches by monkeypatching `app.main.start_scheduler` /
  `stop_scheduler`. Scheduler tests check the job's shape and call `job.func()` directly instead of
  waiting on real time. `scheduler_runner.py` is deliberately untested wiring (~50% coverage).
- Pytest shows a third-party `StarletteDeprecationWarning` (httpx with `TestClient`) — not ours.
- Next: run it end-to-end once (`uvicorn app.main:app`, single process; insert a monitor into local
  Postgres by hand; watch `check_results` fill and `last_checked_at` move). Then auth + API.
