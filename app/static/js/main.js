import { getMe, isLoggedIn, logout } from "./api.js";
import { el } from "./dom.js";
import { createRouter } from "./router.js";
import { loginView, registerView } from "./views/auth.js";
import { monitorDetailView } from "./views/monitor-detail.js";
import { monitorListView } from "./views/monitors.js";

const container = document.getElementById("app");
const nav = document.getElementById("nav");
const navUser = document.getElementById("nav-user");

function placeholder(title, text) {
  return ({ container }) => {
    container.append(
      el("h1", { class: "page-title" }, title),
      el("div", { class: "card" }, el("p", { class: "muted" }, text)),
    );
  };
}

const routes = [
  { path: "/login", public: true, guestOnly: true, view: loginView },
  { path: "/register", public: true, guestOnly: true, view: registerView },
  { path: "/monitors", view: monitorListView },
  { path: "/monitors/new", view: placeholder("Add monitor", "The add form comes in a later step.") },
  { path: "/monitors/:id", view: monitorDetailView },
];

const router = createRouter({ container, routes, loginPath: "/login", homePath: "/monitors" });

async function refreshNav() {
  if (!isLoggedIn()) {
    nav.hidden = true;
    navUser.textContent = "";
    return;
  }
  nav.hidden = false;
  try {
    const me = await getMe();
    navUser.textContent = me.email;
  } catch {
    navUser.textContent = "";
  }
}

document.getElementById("logout").addEventListener("click", () => {
  logout();
  refreshNav();
  router.navigate("/login");
});

window.addEventListener("pulsecheck:unauthorized", () => {
  refreshNav();
  router.navigate("/login");
});

window.addEventListener("hashchange", () => {
  if (nav.hidden === isLoggedIn()) {
    refreshNav();
  }
});

refreshNav();
router.start();
