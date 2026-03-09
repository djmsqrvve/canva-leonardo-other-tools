import assert from 'node:assert/strict';
import test from 'node:test';

import { buildGenerationCommand } from '../src/lib/generation-command.js';

test('buildGenerationCommand uses browser args without shell interpolation', () => {
  const command = buildGenerationCommand({
    rootDir: '/repo',
    assetType: 'social_banner_bg',
    prompt: 'hello"; rm -rf / #',
    useBrowser: true,
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
  });

  assert.deepEqual(command.args, [
    '/repo/dj_msqrvve_brand_system/src/main.py',
    'generate-api',
    'social_banner_bg',
  ]);
  assert.ok(command.env.PYTHONPATH.includes('/repo/dj_msqrvve_brand_system/src'));
});
