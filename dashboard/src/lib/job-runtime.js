import { spawn } from "child_process";
import { randomUUID } from "crypto";

import { extractUrls, getErrorMessage } from "./generate-api-handler.js";
import { buildGenerationCommand } from "./generation-command.js";

const TERMINAL_STATUSES = new Set(["success", "failed", "canceled"]);
const GLOBAL_RUNTIMES_KEY = "__djmsqrvve_job_runtimes";

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

export class JobRuntime {
  /**
   * @param {{
   *   startJob: (job: Record<string, unknown>) => { child?: { kill?: (signal?: string) => boolean }, completion: Promise<{ stdout: string, stderr: string, exitCode: number }> },
   *   now?: () => string,
   *   generateJobId?: () => string,
   *   generateRunId?: () => string,
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

  #dispatch() {
    if (this.activeJobId) {
      return;
    }

    const nextJobId = this.queue.shift();
    if (!nextJobId) {
      return;
    }

    const job = this.jobsById.get(nextJobId);
    if (!job || job.status !== "queued") {
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
      this.#dispatch();
      return;
    }

    if (!startedJob || typeof startedJob.completion?.then !== "function") {
      job.status = "failed";
      job.finishedAt = this.now();
      job.error = "Job runner did not return a completion promise.";
      this.#dispatch();
      return;
    }

    this.activeJobId = nextJobId;
    this.activeChild = startedJob.child || null;

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
      return;
    }

    job.status = "failed";
    job.finishedAt = this.now();
    job.error = getErrorMessage(error);
    job.urls = [];
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
    runtimeMap.set(rootDir, new JobRuntime({ startJob: createProcessRunner(rootDir) }));
  }

  return runtimeMap.get(rootDir);
}
