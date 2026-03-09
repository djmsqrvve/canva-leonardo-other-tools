import path from "path";
import { NextResponse } from "next/server";

import { getJobRuntime } from "@/lib/job-runtime";
import { handleRetryJob } from "@/lib/jobs-api-handler";

function resolveRuntime() {
  const rootDir = path.resolve(process.cwd(), "..");
  return getJobRuntime(rootDir);
}

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ jobId: string }> },
) {
  const { jobId } = await params;
  const response = handleRetryJob({
    jobId,
    runtime: resolveRuntime(),
  });
  return NextResponse.json(response.body, { status: response.status });
}
