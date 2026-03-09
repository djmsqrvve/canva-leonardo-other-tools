import assert from "node:assert/strict";
import test from "node:test";

import {
  extractUrls,
  getErrorMessage,
  validateGeneratePayload,
} from "../src/lib/generation-helpers.js";

test("validateGeneratePayload rejects missing prompt in browser mode", () => {
  const result = validateGeneratePayload({ useBrowser: true, prompt: "" });
  assert.equal(result.ok, false);
  assert.equal(result.response.status, 400);
  assert.equal(result.response.body.error, "Prompt is required for browser generation.");
});

test("validateGeneratePayload rejects missing assetType in api mode", () => {
  const result = validateGeneratePayload({ useBrowser: false, assetType: "" });
  assert.equal(result.ok, false);
  assert.equal(result.response.status, 400);
  assert.equal(result.response.body.error, "assetType is required for API generation.");
});

test("extractUrls returns all http urls from stdout", () => {
  const urls = extractUrls("ok https://a.example/img.png and http://b.example/out.jpg done");
  assert.deepEqual(urls, ["https://a.example/img.png", "http://b.example/out.jpg"]);
});

test("getErrorMessage handles Error and unknown values", () => {
  assert.equal(getErrorMessage(new Error("boom")), "boom");
  assert.equal(getErrorMessage("plain"), "plain");
  assert.equal(getErrorMessage({ no: "message" }), "Unknown generation error.");
});
