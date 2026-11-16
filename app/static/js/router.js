import { isLoggedIn } from "./api.js";

export function createRouter({ container, routes, loginPath, homePath }) {
  let cleanup = null;
  let reloadView = null;

  function parse(hash) {
    const path = hash.replace(/^#/, "") || homePath;
    for (const route of routes) {
      const names = [];
      const pattern = route.path.replace(/:(\w+)/g, (_, name) => {
        names.push(name);
        return "([^/]+)";
      });
      const match = path.match(new RegExp(`^${pattern}$`));
      if (match) {
        const params = Object.fromEntries(names.map((name, i) => [name, decodeURIComponent(match[i + 1])]));
        return { route, params, path };
      }
    }
    return null;
  }

  function navigate(path) {
    if (window.location.hash === `#${path}`) {
      render();
    } else {
      window.location.hash = path;
    }
  }

  function render() {
    const found = parse(window.location.hash);
    if (!found) {
      navigate(homePath);
      return;
    }
    if (!found.route.public && !isLoggedIn()) {
      navigate(loginPath);
      return;
    }
    if (found.route.guestOnly && isLoggedIn()) {
      navigate(homePath);
      return;
    }

    if (cleanup) {
      cleanup();
    }
    cleanup = null;
    reloadView = null;
    container.replaceChildren();
    const result = found.route.view({ container, params: found.params, navigate });
    if (typeof result === "function") {
      cleanup = result;
    } else if (result) {
      cleanup = result.cleanup ?? null;
      reloadView = result.reload ?? null;
    }
  }

  function reload() {
    if (reloadView) {
      reloadView();
    } else {
      render();
    }
  }

  window.addEventListener("hashchange", render);

  return { start: render, navigate, reload };
}
