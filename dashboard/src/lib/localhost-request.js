export const LOCALHOST_ONLY_ERROR =
  "Dashboard API is localhost-only. Open the dashboard from http://127.0.0.1:6767 or http://localhost:6767.";

function normalizeHostCandidate(value) {
  if (typeof value !== "string") {
    return null;
  }

  const candidate = value.split(",")[0]?.trim();
  if (!candidate) {
    return null;
  }

  if (candidate.includes("://")) {
    try {
      return new URL(candidate).hostname.toLowerCase();
    } catch {
      return null;
    }
  }

  if (candidate.startsWith("[")) {
    const endIndex = candidate.indexOf("]");
    if (endIndex > 1) {
      return candidate.slice(1, endIndex).toLowerCase();
    }
  }

  const colonCount = candidate.split(":").length - 1;
  if (colonCount === 1) {
    return candidate.split(":")[0].toLowerCase();
  }
  return candidate.toLowerCase();
}

export function isLoopbackHost(hostname) {
  if (typeof hostname !== "string" || !hostname.trim()) {
    return false;
  }

  const normalized = hostname.trim().toLowerCase();
  if (normalized === "localhost" || normalized.endsWith(".localhost")) {
    return true;
  }
  if (normalized === "::1" || normalized === "[::1]") {
    return true;
  }
  if (normalized === "127.0.0.1" || normalized.startsWith("127.")) {
    return true;
  }
  if (normalized === "::ffff:127.0.0.1" || normalized.startsWith("::ffff:127.")) {
    return true;
  }
  return false;
}

function extractClientAddress(headers) {
  const forwardedFor = headers.get("x-forwarded-for");
  if (forwardedFor) {
    return normalizeHostCandidate(forwardedFor);
  }

  const realIp = headers.get("x-real-ip");
  if (realIp) {
    return normalizeHostCandidate(realIp);
  }

  return null;
}

/**
 * @param {Request} request
 * @returns {{ ok: true } | { ok: false, reason: string }}
 */
export function evaluateLocalRequest(request) {
  const checks = [
    ["request URL", normalizeHostCandidate(request.url)],
    ["Host", normalizeHostCandidate(request.headers.get("x-forwarded-host") || request.headers.get("host"))],
    ["Origin", normalizeHostCandidate(request.headers.get("origin"))],
    ["Referer", normalizeHostCandidate(request.headers.get("referer"))],
    ["client address", extractClientAddress(request.headers)],
  ];

  for (const [label, host] of checks) {
    if (host && !isLoopbackHost(host)) {
      return {
        ok: false,
        reason: `${LOCALHOST_ONLY_ERROR} Rejected ${label} '${host}'.`,
      };
    }
  }

  return { ok: true };
}

/**
 * @param {Request} request
 * @returns {{ status: number, body: { error: string } } | null}
 */
export function guardLocalRequest(request) {
  const result = evaluateLocalRequest(request);
  if (result.ok) {
    return null;
  }
  return {
    status: 403,
    body: { error: result.reason },
  };
}
