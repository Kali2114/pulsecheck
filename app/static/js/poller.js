export function createPoller(load, intervalMs) {
  let timer = null;
  let running = false;
  let stopped = false;

  async function tick() {
    if (stopped || running) {
      return;
    }
    clearTimeout(timer);
    running = true;
    try {
      await load();
    } finally {
      running = false;
      if (!stopped && !document.hidden) {
        timer = setTimeout(tick, intervalMs);
      }
    }
  }

  function onVisibilityChange() {
    if (document.hidden) {
      clearTimeout(timer);
    } else {
      tick();
    }
  }

  document.addEventListener("visibilitychange", onVisibilityChange);

  return {
    start: tick,
    refresh: tick,
    stop() {
      stopped = true;
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    },
  };
}
