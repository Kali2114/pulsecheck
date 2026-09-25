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

**Open decision, settle before the infrastructure layer:** SQLite (simple, matches fridgewatch,
but ephemeral-storage risk on most container platforms and less suited to a growing time-series of
ping results) vs. Postgres (fits AWS RDS's free tier, better for time-series volume, more relevant
on a CV). Lean Postgres given the AWS deployment target, but don't assume — decide explicitly when
you get there.

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

## Current status

Nothing built yet. Fresh scaffold only: directory layout, `pyproject.toml`, pre-commit config,
CI workflow, `requirements.txt`/`requirements-dev.txt`, `.gitignore`. `git init` done, nothing
committed yet. Domain layer is the true starting point — first thing to write is a test, per the
workflow rules above.
