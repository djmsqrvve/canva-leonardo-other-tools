import path from "path";
import { NextResponse } from "next/server";

import { handleHistory } from "@/lib/jobs-api-handler";

export async function GET() {
  const rootDir = path.resolve(process.cwd(), "..");
  const response = handleHistory({ rootDir });
  return NextResponse.json(response.body, { status: response.status });
}
