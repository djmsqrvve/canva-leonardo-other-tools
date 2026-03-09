import assert from 'node:assert/strict';
import test from 'node:test';

import { buildGenerationCommand, resolvePythonPath } from '../src/lib/generation-command.js';

test('buildGenerationCommand uses browser args without shell interpolation', () => {
  const command = buildGenerationCommand({
    rootDir: '/repo',
    assetType: 'social_banner_bg',
    prompt: 'hello"; rm -rf / #',
    useBrowser: true,
  }, {
    existsSync: () => true,
  });

  assert.equal(command.pythonPath, '/repo/dj_msqrvve_brand_system/venv/bin/python');
  assert.deepEqual(command.args, [
    '/repo/dj_msqrvve_brand_system/src/main.py',
    'generate-browser',
    'hello"; rm -rf / #',
    '--headless',
  ]);
});

test('buildGenerationCommand routes api mode by asset type', () => {
  const command = buildGenerationCommand({
    rootDir: '/repo',
    assetType: 'social_banner_bg',
    prompt: 'ignored in api mode',
    useBrowser: false,
  }, {
    existsSync: () => true,
  });

  assert.deepEqual(command.args, [
    '/repo/dj_msqrvve_brand_system/src/main.py',
    'generate-api',
    'social_banner_bg',
  ]);
  assert.ok(command.env.PYTHONPATH.includes('/repo/dj_msqrvve_brand_system/src'));
});

test('buildGenerationCommand includes --run-id when provided in api mode', () => {
  const command = buildGenerationCommand({
    rootDir: '/repo',
    assetType: 'social_banner_bg',
    prompt: 'ignored in api mode',
    useBrowser: false,
    runId: 'run123abc',
  }, {
    existsSync: () => true,
  });

  assert.deepEqual(command.args, [
    '/repo/dj_msqrvve_brand_system/src/main.py',
    'generate-api',
    'social_banner_bg',
    '--run-id',
    'run123abc',
  ]);
});

test('resolvePythonPath falls back to python3 when repo venv is absent', () => {
  const pythonPath = resolvePythonPath('/repo/dj_msqrvve_brand_system', () => false);
  assert.equal(pythonPath, 'python3');
});
