import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execPromise = promisify(exec);

export async function POST(req: NextRequest) {
  try {
    const { assetType, prompt, useBrowser } = await req.json();

    const rootDir = path.resolve(process.cwd(), '..');
    const venvPath = path.join(rootDir, 'dj_msqrvve_brand_system', 'venv', 'bin', 'activate');
    const scriptPath = path.join(rootDir, 'dj_msqrvve_brand_system', 'src', 'main.py');

    let command = '';
    if (useBrowser) {
        // Run with browser (headless for the dashboard)
        command = `source ${venvPath} && export PYTHONPATH=$PYTHONPATH:${path.join(rootDir, 'dj_msqrvve_brand_system', 'src')} && python3 ${scriptPath} generate-browser "${prompt}" --headless`;
    } else {
        // Run with API
        command = `source ${venvPath} && export PYTHONPATH=$PYTHONPATH:${path.join(rootDir, 'dj_msqrvve_brand_system', 'src')} && python3 ${scriptPath} generate-api ${assetType}`;
    }

    const { stdout, stderr } = await execPromise(command, { shell: '/bin/bash' });

    if (stderr && !stdout) {
      return NextResponse.json({ error: stderr }, { status: 500 });
    }

    // Parse the output for image URLs
    const urls = stdout.match(/https?:\/\/[^\s]+/g) || [];

    return NextResponse.json({ 
        message: 'Generation completed', 
        output: stdout,
        urls: urls
    });

  } catch (error: any) {
    console.error('Generation error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
