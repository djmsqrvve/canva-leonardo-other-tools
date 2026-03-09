import path from "path";
import { NextRequest, NextResponse } from "next/server";

import { getJobRuntime } from "@/lib/job-runtime";
import { handleCreateJob, handleListJobs } from "@/lib/jobs-api-handler";

function resolveRuntime() {
  const rootDir = path.resolve(process.cwd(), "..");
  return getJobRuntime(rootDir);
}

export async function POST(req: NextRequest) {
  let payload: Record<string, unknown>;
  try {
    payload = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request payload." }, { status: 400 });
  }

  const response = await handleCreateJob({
    payload,
    runtime: resolveRuntime(),
  });
  return NextResponse.json(response.body, { status: response.status });
}

export async function GET() {
  const response = handleListJobs({
    runtime: resolveRuntime(),
  });
  return NextResponse.json(response.body, { status: response.status });
}
