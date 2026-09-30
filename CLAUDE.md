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
schema-drift bug; don't repeat that), APScheduler (in-process, same as fridgewatch's reminder job).
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

## Current status (2026-09-30)

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
- `PingResult` + `Pinger` Protocol (`app/domain/pinger.py`) — `is_up()` is 2xx/3xx; no status
  code = down.
- `CheckService.check(now)` — pings due monitors with retries (stops at first up), stores one
  result per check, updates `last_checked_at` via `update_monitor`.

Known gaps: `update_monitor` uses `setattr` and bypasses `Monitor` validation — must be handled
when updates arrive via the API. Constructor types in `CheckService` still name the in-memory
repos; switch to Protocols when the DB repos land.

**Persistence layer, in progress:**
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
- Next: `SqlAlchemyMonitorRepository` with integration tests against the test DB (run
  migrations on it, per-test transaction rollback), then a Postgres service container in CI. After that: real httpx `Pinger`, APScheduler wiring,
  then auth + API.
