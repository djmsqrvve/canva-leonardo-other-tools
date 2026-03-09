import path from "path";
import { NextResponse } from "next/server";

import { handleHistory } from "@/lib/jobs-api-handler";
import { guardLocalRequest } from "@/lib/localhost-request";

export async function GET(req: Request) {
  const blocked = guardLocalRequest(req);
  if (blocked) {
    return NextResponse.json(blocked.body, { status: blocked.status });
  }

  const rootDir = path.resolve(process.cwd(), "..");
  const response = handleHistory({ rootDir });
  return NextResponse.json(response.body, { status: response.status });
}
