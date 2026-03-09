import path from 'path';

/**
 * @param {{ rootDir: string; assetType: string; prompt: string; useBrowser: boolean }} input
 */
export function buildGenerationCommand(input) {
  const projectRoot = path.join(input.rootDir, 'dj_msqrvve_brand_system');
  const pythonPath = path.join(projectRoot, 'venv', 'bin', 'python');
  const scriptPath = path.join(projectRoot, 'src', 'main.py');
  const pythonSourcePath = path.join(projectRoot, 'src');

  const args = [scriptPath];
  if (input.useBrowser) {
    args.push('generate-browser', input.prompt, '--headless');
  } else {
    args.push('generate-api', input.assetType);
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
