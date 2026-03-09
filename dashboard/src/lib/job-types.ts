export type JobStatus = "queued" | "running" | "success" | "failed" | "canceled";

export interface DashboardJob {
  id: string;
  status: JobStatus;
  assetType: string;
  prompt: string;
  useBrowser: boolean;
  runId: string | null;
  createdAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  urls: string[];
  error: string | null;
  retryOf?: string;
  queuePosition?: number;
}

export interface LedgerRunSummary {
  runId: string;
  status: "success" | "failed" | "running" | "unknown";
  assetKey: string;
  createdAt: string;
  updatedAt: string;
  imageUrl: string | null;
  designId: string | null;
  exportPath: string | null;
  error: string | null;
}
