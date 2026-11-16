const TOKEN_KEY = "pulsecheck.token";

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === "string" ? detail : `Request failed (${status})`);
    this.status = status;
    this.detail = detail;
  }
}

export function errorMessage(error) {
  if (error instanceof ApiError && Array.isArray(error.detail) && error.detail.length > 0) {
    const first = error.detail[0];
    const fieldName = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : null;
    return fieldName ? `${fieldName}: ${first.msg}` : first.msg;
  }
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "Something went wrong.";
}

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {}
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {}
}

export function isLoggedIn() {
  return getToken() !== null;
}

async function request(path, { method = "GET", json, form, query, authenticated = true } = {}) {
  const url = new URL(path, window.location.origin);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== null && value !== undefined) {
      url.searchParams.set(key, value);
    }
  }

  const headers = {};
  let body;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (form !== undefined) {
    body = new URLSearchParams(form);
  }
  if (authenticated) {
    const token = getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, { method, headers, body });

  if (response.status === 401 && authenticated) {
    clearToken();
    window.dispatchEvent(new CustomEvent("pulsecheck:unauthorized"));
  }
  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, data?.detail);
  }
  return data;
}

export async function login(email, password) {
  const data = await request("/auth/login", {
    method: "POST",
    form: { username: email, password },
    authenticated: false,
  });
  setToken(data.access_token);
}

export function register(email, password) {
  return request("/auth/register", {
    method: "POST",
    json: { email, password },
    authenticated: false,
  });
}

export function logout() {
  clearToken();
}

export const getMe = () => request("/auth/me");

export const listMonitors = () => request("/monitors");

export const getMonitor = (id) => request(`/monitors/${id}`);

export const createMonitor = (monitor) =>
  request("/monitors", { method: "POST", json: monitor });

export const updateMonitor = (id, changes) =>
  request(`/monitors/${id}`, { method: "PATCH", json: changes });

export const deleteMonitor = (id) => request(`/monitors/${id}`, { method: "DELETE" });

export const getCheckResults = (id, since) =>
  request(`/monitors/${id}/check-results`, { query: { since } });

export const getMonitorStats = (id, since) =>
  request(`/monitors/${id}/stats`, { query: { since } });
