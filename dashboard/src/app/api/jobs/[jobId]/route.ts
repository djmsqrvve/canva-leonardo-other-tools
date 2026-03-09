import path from "path";
import { NextResponse } from "next/server";

import { getJobRuntime } from "@/lib/job-runtime";
import { handleGetJob } from "@/lib/jobs-api-handler";
import { guardLocalRequest } from "@/lib/localhost-request";

function resolveRuntime() {
  const rootDir = path.resolve(process.cwd(), "..");
  return getJobRuntime(rootDir);
}

export async function GET(
  req: Request,
  { params }: { params: Promise<{ jobId: string }> },
) {
  const blocked = guardLocalRequest(req);
  if (blocked) {
    return NextResponse.json(blocked.body, { status: blocked.status });
  }

  const { jobId } = await params;
  const response = handleGetJob({
    jobId,
    runtime: resolveRuntime(),
  });
  return NextResponse.json(response.body, { status: response.status });
}
