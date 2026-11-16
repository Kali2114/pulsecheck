import { errorMessage, listMonitors } from "../api.js";
import { el } from "../dom.js";
import { formatDateTime, formatInterval, formatRelative, formatResponseTime } from "../format.js";
import { createPoller } from "../poller.js";

const LIST_REFRESH_MS = 15_000;

export function statusPill(latestCheck) {
  if (latestCheck === null) {
    return el("span", { class: "pill pill--unknown" }, "No checks yet");
  }
  return latestCheck.is_up
    ? el("span", { class: "pill pill--up" }, "Up")
    : el("span", { class: "pill pill--down" }, "Down");
}

function lastCheckText(latestCheck) {
  if (latestCheck === null) {
    return el("span", { class: "muted" }, "Waiting for first check");
  }
  return el(
    "span",
    { title: formatDateTime(latestCheck.checked_at) },
    formatRelative(latestCheck.checked_at),
    el("span", { class: "muted" }, ` · ${formatResponseTime(latestCheck.response_time_ms)}`),
  );
}

function monitorRow(monitor) {
  return el(
    "li",
    {},
    el(
      "a",
      { class: "monitor-row", href: `#/monitors/${monitor.id}` },
      el("div", { class: "monitor-row__status" }, statusPill(monitor.latest_check)),
      el(
        "div",
        { class: "monitor-row__main" },
        el("span", { class: "mono monitor-row__url" }, monitor.url),
        el("span", { class: "muted monitor-row__meta" }, `Every ${formatInterval(monitor.check_interval_seconds)}`),
      ),
      el("div", { class: "monitor-row__last" }, lastCheckText(monitor.latest_check)),
      el("span", { class: "monitor-row__chevron", "aria-hidden": "true" }, "›"),
    ),
  );
}

function summary(monitors) {
  const up = monitors.filter((m) => m.latest_check?.is_up === true).length;
  const down = monitors.filter((m) => m.latest_check?.is_up === false).length;
  const pending = monitors.length - up - down;
  return el(
    "p",
    { class: "muted list-summary" },
    `${up} up · ${down} down`,
    pending ? ` · ${pending} waiting` : null,
  );
}

function emptyState() {
  return el(
    "div",
    { class: "card empty-state" },
    el("h2", {}, "No monitors yet"),
    el("p", { class: "muted" }, "Add a URL and PulseCheck will start checking it on your schedule."),
    el("a", { class: "button", href: "#/monitors/new" }, "Add your first monitor"),
  );
}

export function monitorListView({ container }) {
  const alert = el("div", { class: "alert", role: "alert", hidden: true });
  const body = el("div", {}, el("p", { class: "muted" }, "Loading monitors…"));

  container.append(
    el(
      "div",
      { class: "page-header" },
      el("h1", { class: "page-title" }, "Monitors"),
      el("a", { class: "button", href: "#/monitors/new" }, "+ Add monitor"),
    ),
    alert,
    body,
  );

  const poller = createPoller(async () => {
    try {
      const monitors = await listMonitors();
      alert.hidden = true;
      if (monitors.length === 0) {
        body.replaceChildren(emptyState());
      } else {
        body.replaceChildren(
          summary(monitors),
          el("ul", { class: "card monitor-list" }, monitors.map(monitorRow)),
        );
      }
    } catch (error) {
      if (error.status === 401) {
        return;
      }
      alert.textContent = `Could not refresh monitors: ${errorMessage(error)}`;
      alert.hidden = false;
    }
  }, LIST_REFRESH_MS);

  poller.start();

  return { cleanup: poller.stop, reload: poller.refresh };
}
