import fs from 'fs';
import path from 'path';

/**
 * @param {{ rootDir: string; assetType: string; prompt: string; useBrowser: boolean; runId?: string }} input
 */
function resolveVenvPython(projectRoot) {
  if (process.platform === 'win32') {
    return path.join(projectRoot, 'venv', 'Scripts', 'python.exe');
  }
  return path.join(projectRoot, 'venv', 'bin', 'python');
}

export function resolvePythonPath(projectRoot, existsSync = fs.existsSync) {
  const explicitOverride = process.env.PYTHON_BIN?.trim();
  if (explicitOverride) {
    return explicitOverride;
  }

  const venvPython = resolveVenvPython(projectRoot);
  if (existsSync(venvPython)) {
    return venvPython;
  }

  return 'python3';
}

export function buildGenerationCommand(input, options = {}) {
  const projectRoot = path.join(input.rootDir, 'dj_msqrvve_brand_system');
  const pythonPath = resolvePythonPath(projectRoot, options.existsSync || fs.existsSync);
  const scriptPath = path.join(projectRoot, 'src', 'main.py');
  const pythonSourcePath = path.join(projectRoot, 'src');

  const args = [scriptPath];
  if (input.useBrowser) {
    args.push('generate-browser', input.prompt, '--headless');
  } else {
    args.push('generate-api', input.assetType);
    if (input.runId) {
      args.push('--run-id', input.runId);
    }
  }

  const pyPath = process.env.PYTHONPATH
    ? `${process.env.PYTHONPATH}:${pythonSourcePath}`
    : pythonSourcePath;

  return {
    pythonPath,
    args,
    env: {
      ...process.env,
      PYTHONPATH: pyPath,
    },
  };
}
