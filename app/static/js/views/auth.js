import { errorMessage, login, register } from "../api.js";
import { el } from "../dom.js";

function field({ id, label, type, autocomplete, minlength, hint }) {
  return el(
    "div",
    { class: "field" },
    el("label", { for: id }, label),
    el("input", {
      class: "input",
      id,
      name: id,
      type,
      autocomplete,
      minlength,
      required: true,
    }),
    hint ? el("p", { class: "field__hint" }, hint) : null,
  );
}

function authCard({ title, subtitle, fields, submitLabel, footer, onSubmit }) {
  const alert = el("div", { class: "alert", role: "alert", hidden: true });
  const submit = el("button", { class: "button button--block", type: "submit" }, submitLabel);

  const form = el(
    "form",
    {
      onsubmit: async (event) => {
        event.preventDefault();
        alert.hidden = true;
        submit.disabled = true;
        const original = submit.textContent;
        submit.textContent = "Please wait…";
        try {
          await onSubmit(new FormData(form));
        } catch (error) {
          alert.textContent = errorMessage(error);
          alert.hidden = false;
          submit.disabled = false;
          submit.textContent = original;
        }
      },
    },
    alert,
    fields,
    submit,
  );

  return el(
    "div",
    { class: "auth" },
    el(
      "div",
      { class: "card auth__card" },
      el("h1", { class: "auth__title" }, title),
      el("p", { class: "muted auth__subtitle" }, subtitle),
      form,
    ),
    el("p", { class: "auth__footer muted" }, footer),
  );
}

export function loginView({ container, navigate }) {
  container.append(
    authCard({
      title: "Log in",
      subtitle: "Welcome back to PulseCheck.",
      fields: [
        field({ id: "email", label: "Email", type: "email", autocomplete: "username" }),
        field({ id: "password", label: "Password", type: "password", autocomplete: "current-password" }),
      ],
      submitLabel: "Log in",
      footer: ["No account yet? ", el("a", { href: "#/register" }, "Create one")],
      onSubmit: async (data) => {
        await login(data.get("email"), data.get("password"));
        navigate("/monitors");
      },
    }),
  );
  container.querySelector("#email").focus();
}

export function registerView({ container, navigate }) {
  container.append(
    authCard({
      title: "Create account",
      subtitle: "Start monitoring your endpoints.",
      fields: [
        field({ id: "email", label: "Email", type: "email", autocomplete: "username" }),
        field({
          id: "password",
          label: "Password",
          type: "password",
          autocomplete: "new-password",
          minlength: 8,
          hint: "At least 8 characters.",
        }),
        field({
          id: "password-confirm",
          label: "Confirm password",
          type: "password",
          autocomplete: "new-password",
          minlength: 8,
        }),
      ],
      submitLabel: "Create account",
      footer: ["Already have an account? ", el("a", { href: "#/login" }, "Log in")],
      onSubmit: async (data) => {
        const email = data.get("email");
        const password = data.get("password");
        if (password !== data.get("password-confirm")) {
          throw new Error("Passwords do not match.");
        }
        await register(email, password);
        await login(email, password);
        navigate("/monitors");
      },
    }),
  );
  container.querySelector("#email").focus();
}
