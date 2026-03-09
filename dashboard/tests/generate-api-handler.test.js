import assert from 'node:assert/strict';
import test from 'node:test';

import {
  extractUrls,
  getErrorMessage,
  runGenerateRequest,
  validateGeneratePayload,
} from '../src/lib/generate-api-handler.js';

test('validateGeneratePayload rejects missing prompt in browser mode', () => {
  const result = validateGeneratePayload({ useBrowser: true, prompt: '' });
  assert.equal(result.ok, false);
  assert.equal(result.response.status, 400);
  assert.equal(result.response.body.error, 'Prompt is required for browser generation.');
});

test('validateGeneratePayload rejects missing assetType in api mode', () => {
  const result = validateGeneratePayload({ useBrowser: false, assetType: '' });
  assert.equal(result.ok, false);
  assert.equal(result.response.status, 400);
  assert.equal(result.response.body.error, 'assetType is required for API generation.');
});

test('extractUrls returns all http urls from stdout', () => {
  const urls = extractUrls('ok https://a.example/img.png and http://b.example/out.jpg done');
  assert.deepEqual(urls, ['https://a.example/img.png', 'http://b.example/out.jpg']);
});

test('getErrorMessage handles Error and unknown values', () => {
  assert.equal(getErrorMessage(new Error('boom')), 'boom');
  assert.equal(getErrorMessage('plain'), 'plain');
  assert.equal(getErrorMessage({ no: 'message' }), 'Unknown generation error.');
});

test('runGenerateRequest returns parsed urls on success', async () => {
  const response = await runGenerateRequest({
    payload: { useBrowser: false, assetType: 'social_banner_bg' },
    rootDir: '/repo',
    buildGenerationCommand: () => ({
      pythonPath: '/repo/python',
      args: ['main.py', 'generate-api', 'social_banner_bg'],
      env: {},
    }),
    runProcess: async () => ({
      stdout: 'done https://img.example/a.png',
      stderr: '',
      exitCode: 0,
    }),
  });

  assert.equal(response.status, 200);
  assert.equal(response.body.message, 'Generation completed');
  assert.deepEqual(response.body.urls, ['https://img.example/a.png']);
});

test('runGenerateRequest returns stderr on non-zero exit', async () => {
  const response = await runGenerateRequest({
    payload: { useBrowser: false, assetType: 'social_banner_bg' },
    rootDir: '/repo',
    buildGenerationCommand: () => ({
      pythonPath: '/repo/python',
      args: ['main.py', 'generate-api', 'social_banner_bg'],
      env: {},
    }),
    runProcess: async () => ({
      stdout: 'stdout fallback',
      stderr: 'bad thing',
      exitCode: 1,
    }),
  });

  assert.equal(response.status, 500);
  assert.equal(response.body.error, 'bad thing');
});

test('runGenerateRequest returns normalized error when process throws', async () => {
  const response = await runGenerateRequest({
    payload: { useBrowser: false, assetType: 'social_banner_bg' },
    rootDir: '/repo',
    buildGenerationCommand: () => ({
      pythonPath: '/repo/python',
      args: ['main.py', 'generate-api', 'social_banner_bg'],
      env: {},
    }),
    runProcess: async () => {
      throw new Error('spawn failed');
    },
  });

  assert.equal(response.status, 500);
  assert.equal(response.body.error, 'spawn failed');
});
