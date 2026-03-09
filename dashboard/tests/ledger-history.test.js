import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { readLedgerHistory, resolveLedgerPath } from '../src/lib/ledger-history.js';

function makeTempRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'dj-ledger-history-'));
}

test('readLedgerHistory returns empty array when ledger does not exist', () => {
  const rootDir = makeTempRoot();
  const runs = readLedgerHistory(rootDir);
  assert.deepEqual(runs, []);
});

test('readLedgerHistory aggregates run events and derives statuses', () => {
  const rootDir = makeTempRoot();
  const ledgerPath = resolveLedgerPath(rootDir);
  fs.mkdirSync(path.dirname(ledgerPath), { recursive: true });

  const lines = [
    JSON.stringify({
      timestamp: '2026-03-09T00:00:00Z',
      run_id: 'run_success',
      asset_key: 'social_banner_bg',
      stage: 'generation',
      status: 'started',
    }),
    JSON.stringify({
      timestamp: '2026-03-09T00:00:05Z',
      run_id: 'run_success',
      asset_key: 'social_banner_bg',
      stage: 'generation',
      status: 'success',
      image_url: 'https://example.com/image.png',
    }),
    JSON.stringify({
      timestamp: '2026-03-09T00:00:07Z',
      run_id: 'run_success',
      asset_key: 'social_banner_bg',
      stage: 'export',
      status: 'success',
      export_path: '/tmp/run_success.png',
      design_id: 'design_1',
    }),
    JSON.stringify({
      timestamp: '2026-03-09T00:00:01Z',
      run_id: 'run_failed',
      asset_key: 'profile_avatar',
      stage: 'generation',
      status: 'started',
    }),
    JSON.stringify({
      timestamp: '2026-03-09T00:00:03Z',
      run_id: 'run_failed',
      asset_key: 'profile_avatar',
      stage: 'generation',
      status: 'failed',
      error: 'upstream error',
    }),
    JSON.stringify({
      timestamp: '2026-03-09T00:00:10Z',
      run_id: 'run_running',
      asset_key: 'raid_alert_art',
      stage: 'sync',
      status: 'started',
    }),
  ];

  fs.writeFileSync(ledgerPath, `${lines.join('\n')}\n`, 'utf8');

  const runs = readLedgerHistory(rootDir);
  assert.equal(runs.length, 3);

  assert.equal(runs[0].runId, 'run_running');
  assert.equal(runs[0].status, 'running');
  assert.equal(runs[0].assetKey, 'raid_alert_art');

  const success = runs.find((run) => run.runId === 'run_success');
  assert.equal(success?.status, 'success');
  assert.equal(success?.imageUrl, 'https://example.com/image.png');
  assert.equal(success?.designId, 'design_1');
  assert.equal(success?.exportPath, '/tmp/run_success.png');

  const failed = runs.find((run) => run.runId === 'run_failed');
  assert.equal(failed?.status, 'failed');
  assert.equal(failed?.error, 'upstream error');
});
