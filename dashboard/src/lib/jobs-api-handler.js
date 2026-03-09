import { getErrorMessage, validateGeneratePayload } from "./generate-api-handler.js";
import { readLedgerHistory } from "./ledger-history.js";

function mapTransitionError(error) {
  if (error?.code === "not_found") {
    return { status: 404, body: { error: error.message } };
  }
  if (error?.code === "invalid_transition") {
    return { status: 409, body: { error: error.message } };
  }
  return { status: 500, body: { error: error?.message || "Unexpected job runtime error." } };
}

/**
 * @param {{ payload: Record<string, unknown>, runtime: Record<string, unknown> }} params
 */
export async function handleCreateJob(params) {
  const validation = validateGeneratePayload(params.payload);
  if (!validation.ok) {
    return validation.response;
  }

  try {
    const job = params.runtime.enqueueJob(validation.value);
    return {
      status: 202,
      body: { job },
    };
  } catch (error) {
    return {
      status: 500,
      body: { error: getErrorMessage(error) },
    };
  }
}

/**
 * @param {{ runtime: Record<string, unknown> }} params
 */
export function handleListJobs(params) {
  return {
    status: 200,
    body: {
      jobs: params.runtime.listJobs(),
    },
  };
}

/**
 * @param {{ jobId: string, runtime: Record<string, unknown> }} params
 */
export function handleGetJob(params) {
  const job = params.runtime.getJob(params.jobId);
  if (!job) {
    return {
      status: 404,
      body: { error: `Job '${params.jobId}' not found.` },
    };
  }

  return {
    status: 200,
    body: { job },
  };
}

/**
 * @param {{ jobId: string, runtime: Record<string, unknown> }} params
 */
export function handleCancelJob(params) {
  const result = params.runtime.cancelJob(params.jobId);
  if (!result.ok) {
    return mapTransitionError(result);
  }

  return {
    status: 200,
    body: { job: result.job },
  };
}

/**
 * @param {{ jobId: string, runtime: Record<string, unknown> }} params
 */
export function handleRetryJob(params) {
  const result = params.runtime.retryJob(params.jobId);
  if (!result.ok) {
    return mapTransitionError(result);
  }

  return {
    status: 202,
    body: { job: result.job },
  };
}

/**
 * @param {{ rootDir: string }} params
 */
export function handleHistory(params) {
  try {
    return {
      status: 200,
      body: {
        runs: readLedgerHistory(params.rootDir),
      },
    };
  } catch (error) {
    return {
      status: 500,
      body: { error: getErrorMessage(error) },
    };
  }
}
