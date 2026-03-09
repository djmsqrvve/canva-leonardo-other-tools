import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import { buildGenerationCommand } from '@/lib/generation-command';
import { runGenerateRequest } from '@/lib/generate-api-handler';

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
    const rootDir = path.resolve(process.cwd(), '..');
    const payload = await req.json();
    const response = await runGenerateRequest({
      payload,
      rootDir,
      buildGenerationCommand,
      runProcess,
    });
    return NextResponse.json(response.body, { status: response.status });
  } catch (error: unknown) {
    console.error('Generation error:', error);
    const message = error instanceof Error ? error.message : 'Invalid request payload.';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
