/**
 * @typedef {{
 *   assetType?: unknown,
 *   prompt?: unknown,
 *   useBrowser?: unknown,
 * }} GeneratePayload
 */

/**
 * @typedef {{
 *   status: number,
 *   body: Record<string, unknown>,
 * }} HandlerResponse
 */

/**
 * @param {GeneratePayload} payload
 * @returns {{ ok: true, value: { assetType: string, prompt: string, useBrowser: boolean } } | { ok: false, response: HandlerResponse }}
 */
export function validateGeneratePayload(payload) {
  const useBrowser = Boolean(payload?.useBrowser);
  const prompt = typeof payload?.prompt === "string" ? payload.prompt : "";
  const assetType = typeof payload?.assetType === "string" ? payload.assetType.trim() : "";

  if (useBrowser && !prompt.trim()) {
    return {
      ok: false,
      response: {
        status: 400,
        body: { error: "Prompt is required for browser generation." },
      },
    };
  }

  if (!useBrowser && !assetType) {
    return {
      ok: false,
      response: {
        status: 400,
        body: { error: "assetType is required for API generation." },
      },
    };
  }

  return {
    ok: true,
    value: {
      assetType,
      prompt,
      useBrowser,
    },
  };
}

/**
 * @param {string} stdout
 * @returns {string[]}
 */
export function extractUrls(stdout) {
  return stdout.match(/https?:\/\/[^\s]+/g) || [];
}

/**
 * @param {unknown} error
 * @returns {string}
 */
export function getErrorMessage(error) {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "Unknown generation error.";
}
