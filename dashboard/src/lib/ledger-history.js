import fs from "fs";
import path from "path";

function parseTimestamp(value) {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function asNullableString(value) {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function eventStatusToRunStatus(status) {
  if (status === "success") {
    return "success";
  }
  if (status === "failed") {
    return "failed";
  }
  if (status === "started") {
    return "running";
  }
  return "unknown";
}

/**
 * @param {string} rootDir
 */
export function resolveLedgerPath(rootDir) {
  return path.join(rootDir, "dj_msqrvve_brand_system", "outputs", "ledger.jsonl");
}

/**
 * @param {string} rootDir
 */
export function readLedgerHistory(rootDir) {
  const ledgerPath = resolveLedgerPath(rootDir);
  if (!fs.existsSync(ledgerPath)) {
    return [];
  }

  const raw = fs.readFileSync(ledgerPath, "utf8");
  if (!raw.trim()) {
    return [];
  }

  /** @type {Map<string, Record<string, unknown>>} */
  const runs = new Map();
  const lines = raw.split(/\r?\n/).filter(Boolean);

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    let payload;
    try {
      payload = JSON.parse(line);
    } catch {
      continue;
    }

    const runId = payload?.run_id;
    if (typeof runId !== "string" || runId.length === 0) {
      continue;
    }

    const timestamp = typeof payload.timestamp === "string" ? payload.timestamp : null;
    const timestampMs = timestamp ? parseTimestamp(timestamp) : null;
    const assetKey = asNullableString(payload.asset_key);
    const imageUrl = asNullableString(payload.image_url);
    const designId = asNullableString(payload.design_id);
    const exportPath = asNullableString(payload.export_path);
    const error = asNullableString(payload.error);
    const status = eventStatusToRunStatus(payload.status);

    if (!runs.has(runId)) {
      runs.set(runId, {
        runId,
        status,
        assetKey: assetKey || "unknown",
        createdAt: timestamp || "",
        updatedAt: timestamp || "",
        imageUrl,
        designId,
        exportPath,
        error,
        latestTimestampMs: timestampMs ?? -1,
        latestIndex: index,
      });
      continue;
    }

    const existing = runs.get(runId);
    if (!existing) {
      continue;
    }

    if (assetKey) {
      existing.assetKey = assetKey;
    }
    if (imageUrl) {
      existing.imageUrl = imageUrl;
    }
    if (designId) {
      existing.designId = designId;
    }
    if (exportPath) {
      existing.exportPath = exportPath;
    }
    if (error) {
      existing.error = error;
    }

    if (timestamp && (!existing.createdAt || timestamp < existing.createdAt)) {
      existing.createdAt = timestamp;
    }
    if (timestamp && (!existing.updatedAt || timestamp > existing.updatedAt)) {
      existing.updatedAt = timestamp;
    }

    const shouldUpdateStatus =
      timestampMs !== null
        ? timestampMs > (existing.latestTimestampMs ?? -1) ||
          (timestampMs === existing.latestTimestampMs && index > (existing.latestIndex ?? -1))
        : index > (existing.latestIndex ?? -1);

    if (shouldUpdateStatus) {
      existing.status = status;
      existing.latestTimestampMs = timestampMs ?? existing.latestTimestampMs;
      existing.latestIndex = index;
    }
  }

  return Array.from(runs.values())
    .map((run) => ({
      runId: run.runId,
      status: run.status,
      assetKey: run.assetKey || "unknown",
      createdAt: run.createdAt || run.updatedAt || "",
      updatedAt: run.updatedAt || run.createdAt || "",
      imageUrl: run.imageUrl || null,
      designId: run.designId || null,
      exportPath: run.exportPath || null,
      error: run.error || null,
    }))
    .sort((a, b) => {
      if (a.updatedAt === b.updatedAt) {
        return a.runId < b.runId ? 1 : -1;
      }
      return a.updatedAt < b.updatedAt ? 1 : -1;
    });
}
