import { errorMessage, getCheckResults, getMonitor, getMonitorStats } from "../api.js";
import { buildSeries } from "../chart-data.js";
import { el } from "../dom.js";
import { formatDateTime, formatInterval, formatRelative, formatResponseTime } from "../format.js";
import { createPoller } from "../poller.js";
import { statusPill } from "./monitors.js";

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

const RANGES = [
  { key: "1h", label: "1h", durationMs: HOUR, refreshMs: 15_000, tickStepMs: 10 * MINUTE },
  { key: "24h", label: "24h", durationMs: DAY, refreshMs: 15_000, tickStepMs: 3 * HOUR },
  { key: "7d", label: "7d", durationMs: 7 * DAY - MINUTE, refreshMs: 60_000, tickStepMs: DAY },
];

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function statTile(label, value, hint) {
  return el(
    "div",
    { class: "card stat" },
    el("span", { class: "stat__label" }, label),
    el("span", { class: "stat__value" }, value),
    hint ? el("span", { class: "stat__hint muted" }, hint) : null,
  );
}

function formatUptime(value) {
  if (value === null) {
    return "—";
  }
  return `${value === 100 ? "100" : value.toFixed(2)}%`;
}

function formatAverage(value) {
  return value === null ? "—" : `${Math.round(value)} ms`;
}

function tickLabel(ms, range) {
  const date = new Date(ms);
  if (range.key === "7d") {
    return date.toLocaleDateString(undefined, { weekday: "short", day: "numeric" });
  }
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function clockAlignedTicks(minMs, maxMs, stepMs) {
  const offsetMs = new Date(minMs).getTimezoneOffset() * MINUTE;
  const ticks = [];
  for (let value = Math.ceil((minMs - offsetMs) / stepMs) * stepMs + offsetMs; value <= maxMs; value += stepMs) {
    ticks.push({ value });
  }
  return ticks;
}

function createChart(canvas, range) {
  const muted = cssVar("--text-muted");
  const border = cssVar("--border");
  const accent = cssVar("--accent");
  const down = cssVar("--down");

  return new window.Chart(canvas, {
    type: "line",
    data: {
      datasets: [
        {
          label: "Response time",
          data: [],
          parsing: false,
          borderColor: accent,
          backgroundColor: accent,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.2,
          spanGaps: false,
        },
        {
          label: "Down",
          data: [],
          parsing: false,
          showLine: false,
          borderColor: down,
          backgroundColor: down,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointStyle: "rectRot",
        },
      ],
    },
    options: {
      animation: false,
      maintainAspectRatio: false,
      interaction: { mode: "nearest", axis: "x", intersect: false },
      scales: {
        x: {
          type: "linear",
          grid: { color: border },
          afterBuildTicks: (scale) => {
            scale.ticks = clockAlignedTicks(scale.min, scale.max, range.current.tickStepMs);
          },
          ticks: { color: muted, autoSkip: true, maxRotation: 0, callback: (value) => tickLabel(value, range.current) },
        },
        y: {
          beginAtZero: true,
          grid: { color: border },
          ticks: { color: muted, callback: (value) => `${value} ms` },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => formatDateTime(items[0].parsed.x),
            label: (item) => {
              const point = item.raw;
              if (item.datasetIndex === 1) {
                if (point.checks > 1) {
                  return `Down: ${point.failed} of ${point.checks} checks failed`;
                }
                return `Down · ${formatResponseTime(point.responseTime)}`;
              }
              if (point.checks > 1) {
                return `Avg ${point.y} ms (${point.checks} checks)`;
              }
              return `${point.y} ms`;
            },
          },
        },
      },
    },
  });
}

function rangeControl(onChange, initial) {
  const buttons = RANGES.map((range) =>
    el(
      "button",
      {
        type: "button",
        class: "segmented__button",
        "aria-pressed": range.key === initial.key ? "true" : "false",
        onclick: (event) => {
          for (const button of buttons) {
            button.setAttribute("aria-pressed", button === event.currentTarget ? "true" : "false");
          }
          onChange(range);
        },
      },
      range.label,
    ),
  );
  return el("div", { class: "segmented", role: "group", "aria-label": "Time range" }, buttons);
}

function notFound(container, message) {
  container.replaceChildren(
    el("a", { class: "back-link", href: "#/monitors" }, "← All monitors"),
    el(
      "div",
      { class: "card empty-state" },
      el("h2", {}, "Monitor not found"),
      el("p", { class: "muted" }, message),
      el("a", { class: "button", href: "#/monitors" }, "Back to monitors"),
    ),
  );
}

export function monitorDetailView({ container, params }) {
  const monitorId = params.id;
  const range = { current: RANGES[0] };

  const alert = el("div", { class: "alert", role: "alert", hidden: true });
  const header = el("div", { class: "detail-header" }, el("p", { class: "muted" }, "Loading monitor…"));
  const tiles = el("div", { class: "stats" });
  const canvas = el("canvas", { "aria-label": "Response time chart", role: "img" });
  const chartNote = el("p", { class: "muted chart-note" });
  const chartCard = el(
    "div",
    { class: "card chart-card" },
    el(
      "div",
      { class: "chart-card__header" },
      el("h2", { class: "chart-card__title" }, "Response time"),
      rangeControl((selected) => {
        range.current = selected;
        restartPolling();
      }, range.current),
    ),
    el("div", { class: "chart-card__canvas" }, canvas),
    chartNote,
  );

  container.append(
    el("a", { class: "back-link", href: "#/monitors" }, "← All monitors"),
    header,
    alert,
    tiles,
    chartCard,
  );

  const chart = window.Chart ? createChart(canvas, range) : null;
  if (!chart) {
    chartNote.textContent = "The chart library could not be loaded.";
  }

  let poller = null;
  let gone = false;

  async function load() {
    const selected = range.current;
    const toMs = Date.now();
    const fromMs = toMs - selected.durationMs;
    const since = new Date(fromMs).toISOString();
    try {
      const [monitor, results, stats] = await Promise.all([
        getMonitor(monitorId),
        getCheckResults(monitorId, since),
        getMonitorStats(monitorId, since),
      ]);
      if (selected !== range.current) {
        return;
      }
      alert.hidden = true;
      renderHeader(monitor);
      renderTiles(stats, selected);
      renderChart(results, fromMs, toMs);
    } catch (error) {
      if (error.status === 401) {
        return;
      }
      if (error.status === 404) {
        gone = true;
        poller?.stop();
        chart?.destroy();
        notFound(container, errorMessage(error));
        return;
      }
      alert.textContent = `Could not refresh: ${errorMessage(error)}`;
      alert.hidden = false;
    }
  }

  function renderHeader(monitor) {
    const latest = monitor.latest_check;
    header.replaceChildren(
      el(
        "div",
        { class: "detail-header__title" },
        statusPill(latest),
        el("h1", { class: "mono detail-header__url" }, monitor.url),
      ),
      el(
        "p",
        { class: "muted detail-header__meta" },
        `Every ${formatInterval(monitor.check_interval_seconds)} · timeout ${monitor.timeout_seconds}s · `,
        `${monitor.retry_count} ${monitor.retry_count === 1 ? "attempt" : "attempts"} · `,
        latest
          ? el("span", { title: formatDateTime(latest.checked_at) }, `last check ${formatRelative(latest.checked_at)}`)
          : "no checks yet",
      ),
    );
  }

  function renderTiles(stats, selected) {
    const rangeLabel = `last ${selected.label}`;
    tiles.replaceChildren(
      statTile("Uptime", formatUptime(stats.uptime_percentage), rangeLabel),
      statTile("Avg response", formatAverage(stats.average_response_time_ms), "up checks only"),
      statTile("Checks", stats.check_count.toLocaleString(), rangeLabel),
    );
  }

  function renderChart(results, fromMs, toMs) {
    if (!chart) {
      return;
    }
    const series = buildSeries(results, fromMs, toMs);
    chart.data.datasets[0].data = series.line;
    chart.data.datasets[1].data = series.down;
    chart.options.scales.x.min = fromMs;
    chart.options.scales.x.max = toMs;
    chart.update("none");
    if (results.length === 0) {
      chartNote.textContent = "No checks in this time range yet.";
    } else if (series.bucketed) {
      chartNote.textContent = `${results.length.toLocaleString()} checks, averaged into time buckets. Red markers show buckets with failed checks.`;
    } else {
      chartNote.textContent = "Red markers show failed checks.";
    }
  }

  function restartPolling() {
    if (gone) {
      return;
    }
    poller?.stop();
    poller = createPoller(load, range.current.refreshMs);
    poller.start();
  }

  restartPolling();

  return {
    cleanup: () => {
      poller?.stop();
      chart?.destroy();
    },
    reload: () => poller?.refresh(),
  };
}
