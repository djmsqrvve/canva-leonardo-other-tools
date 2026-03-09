/**
 * @typedef {{
 *   assetType?: unknown,
 *   prompt?: unknown,
 *   useBrowser?: unknown,
 * }} GeneratePayload
 */

/**
 * @typedef {{
 *   pythonPath: string,
 *   args: string[],
 *   env: NodeJS.ProcessEnv,
 * }} GenerationCommand
 */

/**
 * @typedef {{
 *   stdout: string,
 *   stderr: string,
 *   exitCode: number,
 * }} ProcessResult
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
  const prompt = typeof payload?.prompt === 'string' ? payload.prompt : '';
  const assetType = typeof payload?.assetType === 'string' ? payload.assetType.trim() : '';

  if (useBrowser && !prompt.trim()) {
    return {
      ok: false,
      response: {
        status: 400,
        body: { error: 'Prompt is required for browser generation.' },
      },
    };
  }

  if (!useBrowser && !assetType) {
    return {
      ok: false,
      response: {
        status: 400,
        body: { error: 'assetType is required for API generation.' },
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
  if (typeof error === 'string') {
    return error;
  }
  return 'Unknown generation error.';
}

/**
 * @param {{
 *   payload: GeneratePayload,
 *   rootDir: string,
 *   buildGenerationCommand: (input: { rootDir: string, assetType: string, prompt: string, useBrowser: boolean }) => GenerationCommand,
 *   runProcess: (command: string, args: string[], env: NodeJS.ProcessEnv) => Promise<ProcessResult>,
 * }} params
 * @returns {Promise<HandlerResponse>}
 */
export async function runGenerateRequest(params) {
  const validation = validateGeneratePayload(params.payload);
  if (!validation.ok) {
    return validation.response;
  }

  const command = params.buildGenerationCommand({
    rootDir: params.rootDir,
    assetType: validation.value.assetType,
    prompt: validation.value.prompt,
    useBrowser: validation.value.useBrowser,
  });

  try {
    const { stdout, stderr, exitCode } = await params.runProcess(
      command.pythonPath,
      command.args,
      command.env,
    );

    if (exitCode !== 0) {
      return {
        status: 500,
        body: { error: stderr || stdout || 'Generation failed.' },
      };
    }

    return {
      status: 200,
      body: {
        message: 'Generation completed',
        output: stdout,
        urls: extractUrls(stdout),
      },
    };
  } catch (error) {
    return {
      status: 500,
      body: { error: getErrorMessage(error) },
    };
  }
}
