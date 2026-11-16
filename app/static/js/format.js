export function formatInterval(totalSeconds) {
  if (totalSeconds < 60) {
    return `${totalSeconds}s`;
  }
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours && `${hours}h`, minutes && `${minutes}m`, seconds && `${seconds}s`]
    .filter(Boolean)
    .join(" ");
}

export function formatRelative(isoString, now = Date.now()) {
  const seconds = Math.max(0, Math.round((now - new Date(isoString).getTime()) / 1000));
  if (seconds < 5) {
    return "just now";
  }
  if (seconds < 60) {
    return `${seconds}s ago`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} min ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} h ago`;
  }
  return `${Math.floor(hours / 24)} d ago`;
}

export function formatDateTime(isoString) {
  return new Date(isoString).toLocaleString();
}

export function formatResponseTime(ms) {
  return ms === null || ms === undefined ? "no response" : `${ms} ms`;
}
