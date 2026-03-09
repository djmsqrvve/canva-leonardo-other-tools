import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { JobRuntime, resolveJobStatePath } from '../src/lib/job-runtime.js';

function flushAsync() {
  return new Promise((resolve) => {
    setTimeout(resolve, 0);
  });
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function makeTempRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'dj-job-runtime-'));
}

test('JobRuntime dispatches queued jobs serially with a single worker', async () => {
  const first = deferred();
  const second = deferred();
  const starts = [];

  const runtime = new JobRuntime({
    startJob: (job) => {
      starts.push(job.id);
      if (job.id === 'job-1') {
        return {
          child: { kill: () => true },
          completion: first.promise,
        };
      }
      return {
        child: { kill: () => true },
        completion: second.promise,
      };
    },
    now: (() => {
      let index = 0;
      return () => `2026-03-09T00:00:${String(index++).padStart(2, '0')}Z`;
    })(),
    generateJobId: (() => {
      let index = 0;
      const ids = ['job-1', 'job-2'];
      return () => ids[index++];
    })(),
    generateRunId: (() => {
      let index = 0;
      const ids = ['run-1', 'run-2'];
      return () => ids[index++];
    })(),
  });

  runtime.enqueueJob({ assetType: 'social_banner_bg', prompt: '', useBrowser: false });
  runtime.enqueueJob({ assetType: 'profile_avatar', prompt: '', useBrowser: false });

  assert.equal(starts.length, 1);
  assert.equal(runtime.getJob('job-1')?.status, 'running');
  assert.equal(runtime.getJob('job-2')?.status, 'queued');
  assert.equal(runtime.getJob('job-2')?.queuePosition, 1);

  first.resolve({ stdout: 'ok https://example.com/one.png', stderr: '', exitCode: 0 });
  await flushAsync();
  await flushAsync();

  assert.equal(runtime.getJob('job-1')?.status, 'success');
  assert.equal(runtime.getJob('job-2')?.status, 'running');
  assert.equal(starts.length, 2);

  second.resolve({ stdout: 'ok https://example.com/two.png', stderr: '', exitCode: 0 });
  await flushAsync();

  assert.equal(runtime.getJob('job-2')?.status, 'success');
});

test('JobRuntime cancel transitions queued jobs to canceled', async () => {
  const first = deferred();
  const runtime = new JobRuntime({
    startJob: () => ({
      child: { kill: () => true },
      completion: first.promise,
    }),
    generateJobId: (() => {
      let index = 0;
      const ids = ['job-1', 'job-2'];
      return () => ids[index++];
    })(),
    generateRunId: (() => {
      let index = 0;
      const ids = ['run-1', 'run-2'];
      return () => ids[index++];
    })(),
  });

  runtime.enqueueJob({ assetType: 'social_banner_bg', prompt: '', useBrowser: false });
  runtime.enqueueJob({ assetType: 'profile_avatar', prompt: '', useBrowser: false });

  const cancelResult = runtime.cancelJob('job-2');
  assert.equal(cancelResult.ok, true);
  assert.equal(cancelResult.job.status, 'canceled');
  assert.equal(runtime.getJob('job-2')?.queuePosition, undefined);

  first.resolve({ stdout: '', stderr: '', exitCode: 0 });
  await flushAsync();
});

test('JobRuntime cancel kills running process and preserves canceled terminal state', async () => {
  const running = deferred();
  let killCalls = 0;

  const runtime = new JobRuntime({
    startJob: () => ({
      child: {
        kill: () => {
          killCalls += 1;
          return true;
        },
      },
      completion: running.promise,
    }),
    generateJobId: () => 'job-1',
    generateRunId: () => 'run-1',
  });

  runtime.enqueueJob({ assetType: 'social_banner_bg', prompt: '', useBrowser: false });
  assert.equal(runtime.getJob('job-1')?.status, 'running');

  const cancelResult = runtime.cancelJob('job-1');
  assert.equal(cancelResult.ok, true);
  assert.equal(cancelResult.job.status, 'canceled');
  assert.equal(killCalls, 1);

  running.resolve({ stdout: '', stderr: 'process killed', exitCode: 1 });
  await flushAsync();

  assert.equal(runtime.getJob('job-1')?.status, 'canceled');
});

test('JobRuntime retry clones failed job with new runId and retryOf link', async () => {
  const runtime = new JobRuntime({
    startJob: (() => {
      let callIndex = 0;
      return () => {
        callIndex += 1;
        if (callIndex === 1) {
          return {
            child: { kill: () => true },
            completion: Promise.resolve({
              stdout: '',
              stderr: 'failed',
              exitCode: 1,
            }),
          };
        }
        return {
          child: { kill: () => true },
          completion: Promise.resolve({
            stdout: 'ok https://example.com/retry.png',
            stderr: '',
            exitCode: 0,
          }),
        };
      };
    })(),
    generateJobId: (() => {
      let index = 0;
      const ids = ['job-1', 'job-2'];
      return () => ids[index++];
    })(),
    generateRunId: (() => {
      let index = 0;
      const ids = ['run-1', 'run-2'];
      return () => ids[index++];
    })(),
  });

  runtime.enqueueJob({ assetType: 'social_banner_bg', prompt: '', useBrowser: false });
  await flushAsync();

  const failed = runtime.getJob('job-1');
  assert.equal(failed?.status, 'failed');

  const retryResult = runtime.retryJob('job-1');
  assert.equal(retryResult.ok, true);
  assert.equal(retryResult.job.retryOf, 'job-1');
  assert.equal(retryResult.job.runId, 'run-2');

  await flushAsync();
  const retried = runtime.getJob('job-2');
  assert.equal(retried?.status, 'success');
});

test('JobRuntime persists job state for recovery', async () => {
  const rootDir = makeTempRoot();
  const persistencePath = resolveJobStatePath(rootDir);
  const running = deferred();

  const runtime = new JobRuntime({
    startJob: () => ({
      child: { kill: () => true },
      completion: running.promise,
    }),
    generateJobId: () => 'job-1',
    generateRunId: () => 'run-1',
    persistencePath,
  });

  runtime.enqueueJob({ assetType: 'social_banner_bg', prompt: 'prompt', useBrowser: false });

  const persisted = JSON.parse(fs.readFileSync(persistencePath, 'utf8'));
  assert.equal(persisted.version, 1);
  assert.equal(persisted.jobs[0].status, 'running');
  assert.deepEqual(persisted.queue, []);

  running.resolve({ stdout: '', stderr: '', exitCode: 0 });
  await flushAsync();
});

test('JobRuntime restores queued jobs and marks interrupted jobs as failed', async () => {
  const rootDir = makeTempRoot();
  const persistencePath = resolveJobStatePath(rootDir);
  fs.mkdirSync(path.dirname(persistencePath), { recursive: true });
  fs.writeFileSync(
    persistencePath,
    `${JSON.stringify(
      {
        version: 1,
        jobs: [
          {
            id: 'job-1',
            status: 'running',
            assetType: 'social_banner_bg',
            prompt: 'first',
            useBrowser: false,
            runId: 'run-1',
            createdAt: '2026-03-09T00:00:00Z',
            startedAt: '2026-03-09T00:00:01Z',
            finishedAt: null,
            urls: [],
            error: null,
          },
          {
            id: 'job-2',
            status: 'queued',
            assetType: 'profile_avatar',
            prompt: 'second',
            useBrowser: true,
            runId: null,
            createdAt: '2026-03-09T00:00:02Z',
            startedAt: null,
            finishedAt: null,
            urls: [],
            error: null,
          },
        ],
        queue: ['job-2'],
      },
      null,
      2,
    )}\n`,
    'utf8',
  );

  const running = deferred();
  const runtime = new JobRuntime({
    startJob: () => ({
      child: { kill: () => true },
      completion: running.promise,
    }),
    now: () => '2026-03-09T00:00:10Z',
    persistencePath,
  });

  assert.equal(runtime.getJob('job-1')?.status, 'failed');
  assert.match(runtime.getJob('job-1')?.error || '', /Dashboard restarted/);
  assert.equal(runtime.getJob('job-2')?.status, 'running');

  running.resolve({ stdout: '', stderr: '', exitCode: 0 });
  await flushAsync();
});
