import assert from "node:assert/strict";
import test from "node:test";

import {
  LOCALHOST_ONLY_ERROR,
  evaluateLocalRequest,
  guardLocalRequest,
  isLoopbackHost,
} from "../src/lib/localhost-request.js";

function makeRequest(url, headers = {}) {
  return new Request(url, { headers });
}

test("isLoopbackHost recognizes supported localhost values", () => {
  assert.equal(isLoopbackHost("localhost"), true);
  assert.equal(isLoopbackHost("api.localhost"), true);
  assert.equal(isLoopbackHost("127.0.0.1"), true);
  assert.equal(isLoopbackHost("127.0.0.42"), true);
  assert.equal(isLoopbackHost("::1"), true);
  assert.equal(isLoopbackHost("::ffff:127.0.0.1"), true);
  assert.equal(isLoopbackHost("192.168.1.10"), false);
});

test("evaluateLocalRequest allows loopback dashboard requests", () => {
  const result = evaluateLocalRequest(
    makeRequest("http://127.0.0.1:6767/api/jobs", {
      host: "127.0.0.1:6767",
      origin: "http://localhost:6767",
      referer: "http://localhost:6767/",
      "x-forwarded-for": "127.0.0.1",
    }),
  );

  assert.deepEqual(result, { ok: true });
});

test("evaluateLocalRequest rejects remote origin headers", () => {
  const result = evaluateLocalRequest(
    makeRequest("http://127.0.0.1:6767/api/jobs", {
      host: "127.0.0.1:6767",
      origin: "http://192.168.1.20:6767",
    }),
  );

  assert.equal(result.ok, false);
  assert.match(result.reason, /Rejected Origin '192\.168\.1\.20'/);
});

test("evaluateLocalRequest rejects remote forwarded addresses", () => {
  const result = evaluateLocalRequest(
    makeRequest("http://127.0.0.1:6767/api/jobs", {
      host: "127.0.0.1:6767",
      "x-forwarded-for": "10.0.0.15",
    }),
  );

  assert.equal(result.ok, false);
  assert.match(result.reason, /Rejected client address '10\.0\.0\.15'/);
});

test("guardLocalRequest returns a 403 payload for non-local requests", () => {
  const response = guardLocalRequest(
    makeRequest("http://192.168.1.20:6767/api/jobs", {
      host: "192.168.1.20:6767",
    }),
  );

  assert.deepEqual(response, {
    status: 403,
    body: {
      error: `${LOCALHOST_ONLY_ERROR} Rejected request URL '192.168.1.20'.`,
    },
  });
});
