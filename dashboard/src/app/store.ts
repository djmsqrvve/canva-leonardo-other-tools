import { create } from 'zustand';

import type { DashboardJob, LedgerRunSummary } from '@/lib/job-types';

interface BrandStore {
  jobs: DashboardJob[];
  history: LedgerRunSummary[];
  activeJobId: string | null;
  isPolling: boolean;
  setJobs: (jobs: DashboardJob[]) => void;
  upsertJob: (job: DashboardJob) => void;
  setHistory: (runs: LedgerRunSummary[]) => void;
  setActiveJobId: (jobId: string | null) => void;
  setPolling: (value: boolean) => void;
}

export const useBrandStore = create<BrandStore>((set) => ({
  jobs: [],
  history: [],
  activeJobId: null,
  isPolling: false,
  setJobs: (jobs) => set({ jobs }),
  upsertJob: (job) =>
    set((state) => ({
      jobs: state.jobs.some((existing) => existing.id === job.id)
        ? state.jobs.map((existing) => (existing.id === job.id ? job : existing))
        : [job, ...state.jobs],
    })),
  setHistory: (runs) => set({ history: runs }),
  setActiveJobId: (jobId) => set({ activeJobId: jobId }),
  setPolling: (value) => set({ isPolling: value }),
}));
