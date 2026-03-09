import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import { buildGenerationCommand } from '@/lib/generation-command';

function runProcess(command: string, args: string[], env: NodeJS.ProcessEnv) {
  return new Promise<{ stdout: string; stderr: string; exitCode: number }>((resolve, reject) => {
    const child = spawn(command, args, { env });
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    child.on('error', (error) => {
      reject(error);
    });

    child.on('close', (code) => {
      resolve({ stdout, stderr, exitCode: code ?? 1 });
    });
  });
}

export async function POST(req: NextRequest) {
  try {
    const { assetType, prompt, useBrowser } = await req.json();
    if (useBrowser && !prompt) {
      return NextResponse.json({ error: 'Prompt is required for browser generation.' }, { status: 400 });
    }
    if (!useBrowser && !assetType) {
      return NextResponse.json({ error: 'assetType is required for API generation.' }, { status: 400 });
    }

    const rootDir = path.resolve(process.cwd(), '..');
    const command = buildGenerationCommand({
      rootDir,
      assetType,
      prompt,
      useBrowser: Boolean(useBrowser),
    });

    const { stdout, stderr, exitCode } = await runProcess(
      command.pythonPath,
      command.args,
      command.env,
    );

    if (exitCode !== 0) {
      return NextResponse.json({ error: stderr || stdout || 'Generation failed.' }, { status: 500 });
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
