import fs from "fs";
import path from "path";
import { spawn } from "child_process";
import { randomUUID } from "crypto";

import { extractUrls, getErrorMessage } from "./generation-helpers.js";
import { buildGenerationCommand } from "./generation-command.js";

const TERMINAL_STATUSES = new Set(["success", "failed", "canceled"]);
const GLOBAL_RUNTIMES_KEY = "__djmsqrvve_job_runtimes";
const PERSISTED_STATE_VERSION = 1;
const RESTART_FAILURE_MESSAGE =
  "Dashboard restarted while this job was running. Retry the job to continue.";

function nowIso() {
  return new Date().toISOString();
}

function generateJobId() {
  return randomUUID();
}

function generateRunId() {
  return randomUUID().replace(/-/g, "").slice(0, 12);
}

function normalizeCompletion(result) {
  const stdout = typeof result?.stdout === "string" ? result.stdout : "";
  const stderr = typeof result?.stderr === "string" ? result.stderr : "";
  const exitCode = typeof result?.exitCode === "number" ? result.exitCode : 1;
  return { stdout, stderr, exitCode };
}

function normalizeStoredJob(job) {
  if (!job || typeof job !== "object" || typeof job.id !== "string") {
    return null;
  }

  return {
    id: job.id,
    status: typeof job.status === "string" ? job.status : "failed",
    assetType: typeof job.assetType === "string" ? job.assetType : "unknown",
    prompt: typeof job.prompt === "string" ? job.prompt : "",
    useBrowser: Boolean(job.useBrowser),
    runId: typeof job.runId === "string" ? job.runId : null,
    createdAt: typeof job.createdAt === "string" ? job.createdAt : nowIso(),
    startedAt: typeof job.startedAt === "string" ? job.startedAt : null,
    finishedAt: typeof job.finishedAt === "string" ? job.finishedAt : null,
    urls: Array.isArray(job.urls) ? job.urls.filter((value) => typeof value === "string") : [],
    error: typeof job.error === "string" ? job.error : null,
    retryOf: typeof job.retryOf === "string" ? job.retryOf : undefined,
  };
}

function serializePersistedState(jobOrder, jobsById, queue) {
  return {
    version: PERSISTED_STATE_VERSION,
    jobs: jobOrder.map((jobId) => jobsById.get(jobId)).filter(Boolean),
    queue,
  };
}

export function resolveJobStatePath(rootDir) {
  return path.join(rootDir, "dj_msqrvve_brand_system", "outputs", "dashboard-jobs.json");
}

export class JobRuntime {
  /**
   * @param {{
   *   startJob: (job: Record<string, unknown>) => { child?: { kill?: (signal?: string) => boolean }, completion: Promise<{ stdout: string, stderr: string, exitCode: number }> },
   *   now?: () => string,
   *   generateJobId?: () => string,
   *   generateRunId?: () => string,
   *   persistencePath?: string | null,
   * }} options
   */
  constructor(options) {
    if (!options?.startJob) {
      throw new Error("JobRuntime requires a startJob function.");
    }

    this.startJob = options.startJob;
    this.now = options.now || nowIso;
    this.makeJobId = options.generateJobId || generateJobId;
    this.makeRunId = options.generateRunId || generateRunId;
    this.persistencePath = options.persistencePath || null;

    /** @type {Map<string, Record<string, unknown>>} */
    this.jobsById = new Map();
    /** @type {string[]} */
    this.jobOrder = [];
    /** @type {string[]} */
    this.queue = [];

    /** @type {string | null} */
    this.activeJobId = null;
    /** @type {{ kill?: (signal?: string) => boolean } | null} */
    this.activeChild = null;

    this.#loadPersistedState();
    this.#dispatch();
  }

  /**
   * @param {{ assetType: string, prompt: string, useBrowser: boolean }} input
   * @param {{ retryOf?: string }} [meta]
   */
  enqueueJob(input, meta = {}) {
    const id = this.makeJobId();
    const isBrowser = Boolean(input.useBrowser);
    const createdAt = this.now();
    const runId = isBrowser ? null : this.makeRunId();

    const job = {
      id,
      status: "queued",
      assetType: input.assetType,
      prompt: input.prompt,
      useBrowser: isBrowser,
      runId,
      createdAt,
      startedAt: null,
      finishedAt: null,
      urls: [],
      error: null,
      retryOf: meta.retryOf,
    };

    this.jobsById.set(id, job);
    this.jobOrder.unshift(id);
    this.queue.push(id);
    this.#persist();
    this.#dispatch();

    return this.#serialize(job);
  }

  listJobs() {
    return this.jobOrder
      .map((jobId) => this.jobsById.get(jobId))
      .filter((job) => Boolean(job))
      .map((job) => this.#serialize(job));
  }

  /**
   * @param {string} jobId
   */
  getJob(jobId) {
    const job = this.jobsById.get(jobId);
    if (!job) {
      return null;
    }
    return this.#serialize(job);
  }

  /**
   * @param {string} jobId
   */
  cancelJob(jobId) {
    const job = this.jobsById.get(jobId);
    if (!job) {
      return { ok: false, code: "not_found", message: `Job '${jobId}' not found.` };
    }

    if (TERMINAL_STATUSES.has(job.status)) {
      return {
        ok: false,
        code: "invalid_transition",
        message: `Job '${jobId}' is already terminal (${job.status}).`,
      };
    }

    if (job.status === "queued") {
      this.queue = this.queue.filter((queuedId) => queuedId !== jobId);
      job.status = "canceled";
      job.finishedAt = this.now();
      job.error = null;
      this.#persist();
      return { ok: true, job: this.#serialize(job) };
    }

    if (job.status === "running") {
      job.status = "canceled";
      job.finishedAt = this.now();
      job.error = null;

      try {
        if (this.activeJobId === jobId && this.activeChild?.kill) {
          this.activeChild.kill("SIGTERM");
        }
      } catch (error) {
        job.error = getErrorMessage(error);
      }

      this.#persist();
      return { ok: true, job: this.#serialize(job) };
    }

    return {
      ok: false,
      code: "invalid_transition",
      message: `Job '${jobId}' cannot be canceled from status '${job.status}'.`,
    };
  }

  /**
   * @param {string} jobId
   */
  retryJob(jobId) {
    const job = this.jobsById.get(jobId);
    if (!job) {
      return { ok: false, code: "not_found", message: `Job '${jobId}' not found.` };
    }

    if (!["failed", "canceled"].includes(job.status)) {
      return {
        ok: false,
        code: "invalid_transition",
        message: `Job '${jobId}' cannot be retried from status '${job.status}'.`,
      };
    }

    const retriedJob = this.enqueueJob(
      {
        assetType: job.assetType,
        prompt: job.prompt,
        useBrowser: job.useBrowser,
      },
      { retryOf: jobId },
    );

    return { ok: true, job: retriedJob };
  }

  #loadPersistedState() {
    if (!this.persistencePath || !fs.existsSync(this.persistencePath)) {
      return;
    }

    try {
      const raw = fs.readFileSync(this.persistencePath, "utf8");
      if (!raw.trim()) {
        return;
      }

      const parsed = JSON.parse(raw);
      const persistedJobs = Array.isArray(parsed?.jobs) ? parsed.jobs : [];
      const persistedQueue = Array.isArray(parsed?.queue)
        ? parsed.queue.filter((jobId) => typeof jobId === "string")
        : [];

      let recovered = false;
      for (const storedJob of persistedJobs) {
        const normalized = normalizeStoredJob(storedJob);
        if (!normalized) {
          continue;
        }

        // A prior Node process cannot hand off a live child process safely, so interrupted
        // work is surfaced as retryable failure while queued work is preserved.
        if (normalized.status === "running") {
          normalized.status = "failed";
          normalized.finishedAt = this.now();
          normalized.error = RESTART_FAILURE_MESSAGE;
          normalized.urls = [];
          recovered = true;
        }

        this.jobsById.set(normalized.id, normalized);
        this.jobOrder.push(normalized.id);
      }

      const queuedFromDisk = persistedQueue.filter((jobId) => this.jobsById.get(jobId)?.status === "queued");
      const missingQueuedJobs = this.jobOrder.filter(
        (jobId) => this.jobsById.get(jobId)?.status === "queued" && !queuedFromDisk.includes(jobId),
      );
      this.queue = [...queuedFromDisk, ...missingQueuedJobs];

      if (recovered || missingQueuedJobs.length > 0) {
        this.#persist();
      }
    } catch (error) {
      console.warn("Unable to restore dashboard job state:", getErrorMessage(error));
    }
  }

  #persist() {
    if (!this.persistencePath) {
      return;
    }

    const payload = serializePersistedState(this.jobOrder, this.jobsById, this.queue);
    fs.mkdirSync(path.dirname(this.persistencePath), { recursive: true });
    const tmpPath = `${this.persistencePath}.tmp`;
    fs.writeFileSync(tmpPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
    fs.renameSync(tmpPath, this.persistencePath);
  }

  #dispatch() {
    if (this.activeJobId) {
      return;
    }

    const nextJobId = this.queue.shift();
    if (!nextJobId) {
      this.#persist();
      return;
    }

    const job = this.jobsById.get(nextJobId);
    if (!job || job.status !== "queued") {
      this.#persist();
      this.#dispatch();
      return;
    }

    job.status = "running";
    job.startedAt = this.now();
    job.error = null;

    /** @type {{ child?: { kill?: (signal?: string) => boolean }, completion: Promise<{ stdout: string, stderr: string, exitCode: number }> }} */
    let startedJob;
    try {
      startedJob = this.startJob(job);
    } catch (error) {
      job.status = "failed";
      job.finishedAt = this.now();
      job.error = getErrorMessage(error);
      this.#persist();
      this.#dispatch();
      return;
    }

    if (!startedJob || typeof startedJob.completion?.then !== "function") {
      job.status = "failed";
      job.finishedAt = this.now();
      job.error = "Job runner did not return a completion promise.";
      this.#persist();
      this.#dispatch();
      return;
    }

    this.activeJobId = nextJobId;
    this.activeChild = startedJob.child || null;
    this.#persist();

    startedJob.completion
      .then((result) => {
        this.#completeJob(nextJobId, result);
      })
      .catch((error) => {
        this.#failJob(nextJobId, error);
      })
      .finally(() => {
        if (this.activeJobId === nextJobId) {
          this.activeJobId = null;
          this.activeChild = null;
        }
        this.#persist();
        this.#dispatch();
      });
  }

  #completeJob(jobId, result) {
    const job = this.jobsById.get(jobId);
    if (!job) {
      return;
    }

    if (job.status === "canceled") {
      if (!job.finishedAt) {
        job.finishedAt = this.now();
      }
      this.#persist();
      return;
    }

    const completion = normalizeCompletion(result);
    if (completion.exitCode === 0) {
      job.status = "success";
      job.error = null;
      job.urls = extractUrls(completion.stdout);
    } else {
      job.status = "failed";
      job.error = completion.stderr || completion.stdout || "Generation failed.";
      job.urls = [];
    }
    job.finishedAt = this.now();
    this.#persist();
  }

  #failJob(jobId, error) {
    const job = this.jobsById.get(jobId);
    if (!job) {
      return;
    }

    if (job.status === "canceled") {
      if (!job.finishedAt) {
        job.finishedAt = this.now();
      }
      this.#persist();
      return;
    }

    job.status = "failed";
    job.finishedAt = this.now();
    job.error = getErrorMessage(error);
    job.urls = [];
    this.#persist();
  }

  #serialize(job) {
    if (!job) {
      return null;
    }

    const queuePosition =
      job.status === "queued" ? this.queue.findIndex((queuedId) => queuedId === job.id) + 1 : 0;

    const serialized = {
      id: job.id,
      status: job.status,
      assetType: job.assetType,
      prompt: job.prompt,
      useBrowser: job.useBrowser,
      runId: job.runId,
      createdAt: job.createdAt,
      startedAt: job.startedAt,
      finishedAt: job.finishedAt,
      urls: job.urls,
      error: job.error,
      retryOf: job.retryOf,
    };

    if (queuePosition > 0) {
      serialized.queuePosition = queuePosition;
    }
    if (!serialized.retryOf) {
      delete serialized.retryOf;
    }
    return serialized;
  }
}

/**
 * @param {string} rootDir
 */
export function createProcessRunner(rootDir) {
  return (job) => {
    const command = buildGenerationCommand({
      rootDir,
      assetType: job.assetType,
      prompt: job.prompt,
      useBrowser: job.useBrowser,
      runId: job.runId || undefined,
    });

    const child = spawn(command.pythonPath, command.args, {
      env: command.env,
    });

    let stdout = "";
    let stderr = "";

    const completion = new Promise((resolve, reject) => {
      child.stdout?.on("data", (chunk) => {
        stdout += chunk.toString();
      });

      child.stderr?.on("data", (chunk) => {
        stderr += chunk.toString();
      });

      child.on("error", (error) => {
        reject(error);
      });

      child.on("close", (code) => {
        resolve({
          stdout,
          stderr,
          exitCode: code ?? 1,
        });
      });
    });

    return { child, completion };
  };
}

/**
 * @param {string} rootDir
 */
export function getJobRuntime(rootDir) {
  if (!globalThis[GLOBAL_RUNTIMES_KEY]) {
    globalThis[GLOBAL_RUNTIMES_KEY] = new Map();
  }

  const runtimeMap = globalThis[GLOBAL_RUNTIMES_KEY];
  if (!runtimeMap.has(rootDir)) {
    runtimeMap.set(
      rootDir,
      new JobRuntime({
        startJob: createProcessRunner(rootDir),
        persistencePath: resolveJobStatePath(rootDir),
      }),
    );
  }

  return runtimeMap.get(rootDir);
}
