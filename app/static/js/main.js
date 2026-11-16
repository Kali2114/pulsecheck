import { getMe, isLoggedIn, logout } from "./api.js";
import { createRouter } from "./router.js";
import { loginView, registerView } from "./views/auth.js";
import { monitorDetailView } from "./views/monitor-detail.js";
import { monitorCreateView, monitorEditView } from "./views/monitor-form.js";
import { monitorListView } from "./views/monitors.js";

const container = document.getElementById("app");
const nav = document.getElementById("nav");
const navUser = document.getElementById("nav-user");

const routes = [
  { path: "/login", public: true, guestOnly: true, view: loginView },
  { path: "/register", public: true, guestOnly: true, view: registerView },
  { path: "/monitors", view: monitorListView },
  { path: "/monitors/new", view: monitorCreateView },
  { path: "/monitors/:id", view: monitorDetailView },
  { path: "/monitors/:id/edit", view: monitorEditView },
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
