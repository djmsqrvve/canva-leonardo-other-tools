import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  handleCancelJob,
  handleCreateJob,
  handleGetJob,
  handleHistory,
  handleListJobs,
  handleRetryJob,
} from '../src/lib/jobs-api-handler.js';
import { resolveLedgerPath } from '../src/lib/ledger-history.js';

function makeTempRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'dj-jobs-handler-'));
}

test('handleCreateJob returns validation errors for bad payloads', async () => {
  const runtime = {
    enqueueJob: () => {
      throw new Error('should not run');
    },
  };

  const browserError = await handleCreateJob({
    payload: { useBrowser: true, prompt: '' },
    runtime,
  });
  assert.equal(browserError.status, 400);
  assert.equal(browserError.body.error, 'Prompt is required for browser generation.');

  const apiError = await handleCreateJob({
    payload: { useBrowser: false, assetType: '' },
    runtime,
  });
  assert.equal(apiError.status, 400);
  assert.equal(apiError.body.error, 'assetType is required for API generation.');
});

test('handleCreateJob enqueues normalized payload and returns 202', async () => {
  /** @type {Record<string, unknown>[]} */
  const calls = [];
  const runtime = {
    enqueueJob: (payload) => {
      calls.push(payload);
      return {
        id: 'job_1',
        status: 'queued',
        assetType: payload.assetType,
        prompt: payload.prompt,
        useBrowser: payload.useBrowser,
      };
    },
  };

  const response = await handleCreateJob({
    payload: { useBrowser: false, assetType: ' social_banner_bg ', prompt: 42 },
    runtime,
  });

  assert.equal(response.status, 202);
  assert.equal(response.body.job.id, 'job_1');
  assert.equal(calls[0].assetType, 'social_banner_bg');
  assert.equal(calls[0].prompt, '');
});

test('handleListJobs and handleGetJob return expected responses', () => {
  const runtime = {
    listJobs: () => [{ id: 'job_1', status: 'queued' }],
    getJob: (jobId) => (jobId === 'job_1' ? { id: 'job_1', status: 'queued' } : null),
  };

  const listResponse = handleListJobs({ runtime });
  assert.equal(listResponse.status, 200);
  assert.equal(listResponse.body.jobs.length, 1);

  const getOk = handleGetJob({ jobId: 'job_1', runtime });
  assert.equal(getOk.status, 200);
  assert.equal(getOk.body.job.id, 'job_1');

  const getMissing = handleGetJob({ jobId: 'missing', runtime });
  assert.equal(getMissing.status, 404);
});

test('handleCancelJob maps not-found and invalid-transition errors', () => {
  const runtime = {
    cancelJob: (jobId) => {
      if (jobId === 'missing') {
        return { ok: false, code: 'not_found', message: 'missing' };
      }
      if (jobId === 'terminal') {
        return { ok: false, code: 'invalid_transition', message: 'terminal' };
      }
      return { ok: true, job: { id: jobId, status: 'canceled' } };
    },
  };

  assert.equal(handleCancelJob({ jobId: 'missing', runtime }).status, 404);
  assert.equal(handleCancelJob({ jobId: 'terminal', runtime }).status, 409);

  const success = handleCancelJob({ jobId: 'job_1', runtime });
  assert.equal(success.status, 200);
  assert.equal(success.body.job.status, 'canceled');
});

test('handleRetryJob maps not-found and invalid-transition errors', () => {
  const runtime = {
    retryJob: (jobId) => {
      if (jobId === 'missing') {
        return { ok: false, code: 'not_found', message: 'missing' };
      }
      if (jobId === 'running') {
        return { ok: false, code: 'invalid_transition', message: 'running' };
      }
      return { ok: true, job: { id: 'job_2', status: 'queued', retryOf: jobId } };
    },
  };

  assert.equal(handleRetryJob({ jobId: 'missing', runtime }).status, 404);
  assert.equal(handleRetryJob({ jobId: 'running', runtime }).status, 409);

  const success = handleRetryJob({ jobId: 'job_1', runtime });
  assert.equal(success.status, 202);
  assert.equal(success.body.job.retryOf, 'job_1');
});

test('handleHistory returns aggregated ledger runs', () => {
  const rootDir = makeTempRoot();
  const ledgerPath = resolveLedgerPath(rootDir);
  fs.mkdirSync(path.dirname(ledgerPath), { recursive: true });
  fs.writeFileSync(
    ledgerPath,
    `${JSON.stringify({
      timestamp: '2026-03-09T00:00:00Z',
      run_id: 'run_1',
      asset_key: 'social_banner_bg',
      stage: 'generation',
      status: 'success',
      image_url: 'https://example.com/a.png',
    })}\n`,
    'utf8',
  );

  const response = handleHistory({ rootDir });
  assert.equal(response.status, 200);
  assert.equal(response.body.runs.length, 1);
  assert.equal(response.body.runs[0].runId, 'run_1');
});
