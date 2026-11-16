import { createMonitor, errorMessage, getMonitor, updateMonitor } from "../api.js";
import { el } from "../dom.js";

const UNITS = [
  { key: "seconds", label: "seconds", factor: 1 },
  { key: "minutes", label: "minutes", factor: 60 },
  { key: "hours", label: "hours", factor: 3600 },
];

const MIN_INTERVAL_SECONDS = 10;
const MAX_INTERVAL_SECONDS = 86400;
const DEFAULTS = { url: "", check_interval_seconds: 60, timeout_seconds: 10, retry_count: 1 };

function splitInterval(seconds) {
  const unit = [...UNITS].reverse().find((u) => seconds % u.factor === 0) ?? UNITS[0];
  return { value: seconds / unit.factor, unit: unit.key };
}

function numberField({ id, label, value, min, max, hint, suffix }) {
  return el(
    "div",
    { class: "field" },
    el("label", { for: id }, label),
    el(
      "div",
      { class: "input-group" },
      el("input", { class: "input", id, name: id, type: "number", inputmode: "numeric", min, max, step: 1, value, required: true }),
      suffix ? el("span", { class: "input-group__suffix muted" }, suffix) : null,
    ),
    hint ? el("p", { class: "field__hint" }, hint) : null,
  );
}

function intervalField(seconds) {
  const { value, unit } = splitInterval(seconds);
  return el(
    "div",
    { class: "field" },
    el("label", { for: "interval-value" }, "Check every"),
    el(
      "div",
      { class: "input-group" },
      el("input", { class: "input", id: "interval-value", name: "interval-value", type: "number", inputmode: "numeric", min: 1, step: 1, value, required: true }),
      el(
        "select",
        { class: "input input--select", id: "interval-unit", name: "interval-unit", "aria-label": "Interval unit" },
        UNITS.map((u) => el("option", { value: u.key, selected: u.key === unit }, u.label)),
      ),
    ),
    el("p", { class: "field__hint" }, "Between 10 seconds and 24 hours."),
  );
}

function readForm(form) {
  const data = new FormData(form);
  const unit = UNITS.find((u) => u.key === data.get("interval-unit"));
  const intervalSeconds = Number(data.get("interval-value")) * unit.factor;
  if (!Number.isInteger(intervalSeconds) || intervalSeconds < MIN_INTERVAL_SECONDS || intervalSeconds > MAX_INTERVAL_SECONDS) {
    throw new Error("Check interval must be between 10 seconds and 24 hours.");
  }
  return {
    url: data.get("url").trim(),
    check_interval_seconds: intervalSeconds,
    timeout_seconds: Number(data.get("timeout")),
    retry_count: Number(data.get("attempts")),
  };
}

function changedFields(original, updated) {
  return Object.fromEntries(Object.entries(updated).filter(([key, value]) => original[key] !== value));
}

function renderForm(container, { title, submitLabel, monitor, cancelHref, onSubmit }) {
  const alert = el("div", { class: "alert", role: "alert", hidden: true });
  const submit = el("button", { class: "button", type: "submit" }, submitLabel);

  const form = el(
    "form",
    {
      class: "card form-card",
      onsubmit: async (event) => {
        event.preventDefault();
        alert.hidden = true;
        submit.disabled = true;
        try {
          await onSubmit(readForm(form));
        } catch (error) {
          alert.textContent = errorMessage(error);
          alert.hidden = false;
          submit.disabled = false;
        }
      },
    },
    alert,
    el(
      "div",
      { class: "field" },
      el("label", { for: "url" }, "URL"),
      el("input", {
        class: "input mono",
        id: "url",
        name: "url",
        type: "url",
        placeholder: "https://example.com/health",
        value: monitor.url,
        required: true,
      }),
      el("p", { class: "field__hint" }, "PulseCheck sends a GET request; any 2xx or 3xx answer counts as up."),
    ),
    intervalField(monitor.check_interval_seconds),
    el(
      "div",
      { class: "form-row" },
      numberField({ id: "timeout", label: "Timeout", value: monitor.timeout_seconds, min: 1, max: 60, suffix: "seconds", hint: "1–60 seconds." }),
      numberField({ id: "attempts", label: "Attempts per check", value: monitor.retry_count, min: 1, hint: "1 means no retries." }),
    ),
    el(
      "div",
      { class: "form-actions" },
      el("a", { class: "button button--ghost", href: cancelHref }, "Cancel"),
      submit,
    ),
  );

  container.replaceChildren(
    el("a", { class: "back-link", href: cancelHref }, "← Back"),
    el("h1", { class: "page-title" }, title),
    form,
  );
  form.querySelector("#url").focus();
}

export function monitorCreateView({ container, navigate }) {
  renderForm(container, {
    title: "Add monitor",
    submitLabel: "Add monitor",
    monitor: DEFAULTS,
    cancelHref: "#/monitors",
    onSubmit: async (values) => {
      const created = await createMonitor(values);
      navigate(`/monitors/${created.id}`);
    },
  });
}

export function monitorEditView({ container, params, navigate }) {
  let active = true;
  container.append(el("p", { class: "muted" }, "Loading monitor…"));

  getMonitor(params.id)
    .then((monitor) => {
      if (!active) {
        return;
      }
      renderForm(container, {
        title: "Edit monitor",
        submitLabel: "Save changes",
        monitor,
        cancelHref: `#/monitors/${monitor.id}`,
        onSubmit: async (values) => {
          const changes = changedFields(monitor, values);
          if (Object.keys(changes).length > 0) {
            await updateMonitor(monitor.id, changes);
          }
          navigate(`/monitors/${monitor.id}`);
        },
      });
    })
    .catch((error) => {
      if (!active || error.status === 401) {
        return;
      }
      container.replaceChildren(
        el("a", { class: "back-link", href: "#/monitors" }, "← All monitors"),
        el("div", { class: "alert", role: "alert" }, errorMessage(error)),
      );
    });

  return () => {
    active = false;
  };
}
