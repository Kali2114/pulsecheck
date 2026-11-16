import { getMe, isLoggedIn, logout } from "./api.js";
import { el } from "./dom.js";
import { createRouter } from "./router.js";

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
  { path: "/login", public: true, guestOnly: true, view: placeholder("Log in", "Login form comes next.") },
  { path: "/register", public: true, guestOnly: true, view: placeholder("Create account", "Register form comes next.") },
  { path: "/monitors", view: placeholder("Monitors", "Monitor list comes next.") },
  {
    path: "/monitors/:id",
    view: ({ container, params }) =>
      placeholder(`Monitor ${params.id}`, "Monitor detail comes later.")({ container }),
  },
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
