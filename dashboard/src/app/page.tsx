'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useBrandStore } from './store';
import type { DashboardJob, LedgerRunSummary, JobStatus } from '@/lib/job-types';
import {
  ChevronRight,
  Clock3,
  Image as ImageIcon,
  Layers,
  Layout,
  Loader2,
  Palette,
  Sparkles,
  XCircle,
  RotateCcw,
  Zap,
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const POLL_INTERVAL_MS = 2000;

const ASSET_TYPES = [
  { id: 'social_banner_bg', label: 'Social Banner', icon: Layout },
  { id: 'profile_avatar', label: 'Profile Avatar', icon: Palette },
  { id: 'raid_alert_art', label: 'Raid Alert', icon: Zap },
  { id: 'helix2000_tileset_grass', label: 'Helix 2000 Tileset', icon: Layers },
  { id: 'bevy_skybox', label: 'Bevy Skybox', icon: Sparkles },
];

interface JobsApiResponse {
  jobs?: DashboardJob[];
  error?: string;
}

interface JobApiResponse {
  job?: DashboardJob;
  error?: string;
}

interface HistoryApiResponse {
  runs?: LedgerRunSummary[];
  error?: string;
}

const STATUS_CLASS: Record<JobStatus, string> = {
  queued: 'bg-blue-900/40 text-blue-200',
  running: 'bg-amber-900/40 text-amber-200',
  success: 'bg-emerald-900/40 text-emerald-200',
  failed: 'bg-rose-900/40 text-rose-200',
  canceled: 'bg-zinc-800 text-zinc-300',
};

function formatTime(timestamp: string | null) {
  if (!timestamp) {
    return '--:--:--';
  }
  const value = new Date(timestamp);
  if (Number.isNaN(value.getTime())) {
    return '--:--:--';
  }
  return value.toLocaleTimeString();
}

function formatJobTitle(job: DashboardJob) {
  return job.assetType.replaceAll('_', ' ');
}

export default function DashboardPage() {
  const {
    jobs,
    history,
    activeJobId,
    isPolling,
    setJobs,
    upsertJob,
    setHistory,
    setActiveJobId,
    setPolling,
  } = useBrandStore();

  const [selectedAsset, setSelectedAsset] = useState(ASSET_TYPES[0].id);
  const [prompt, setPrompt] = useState('');
  const [useBrowser, setUseBrowser] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionJobId, setActionJobId] = useState<string | null>(null);
  const refreshLock = useRef(false);

  const isGenerateDisabled = isSubmitting || (useBrowser && !prompt.trim());

  const successfulJobs = useMemo(
    () => jobs.filter((job) => job.status === 'success' && job.urls.length > 0),
    [jobs],
  );

  const refreshData = useCallback(async () => {
    if (refreshLock.current) {
      return;
    }
    refreshLock.current = true;
    setPolling(true);

    try {
      const [jobsResponse, historyResponse] = await Promise.all([
        fetch('/api/jobs'),
        fetch('/api/jobs/history'),
      ]);

      if (jobsResponse.ok) {
        const jobsPayload = (await jobsResponse.json()) as JobsApiResponse;
        if (Array.isArray(jobsPayload.jobs)) {
          setJobs(jobsPayload.jobs);
        }
      }

      if (historyResponse.ok) {
        const historyPayload = (await historyResponse.json()) as HistoryApiResponse;
        if (Array.isArray(historyPayload.runs)) {
          setHistory(historyPayload.runs);
        }
      }
    } catch (error) {
      console.error('Polling error:', error);
    } finally {
      setPolling(false);
      refreshLock.current = false;
    }
  }, [setHistory, setJobs, setPolling]);

  useEffect(() => {
    void refreshData();
    const timer = window.setInterval(() => {
      void refreshData();
    }, POLL_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
    };
  }, [refreshData]);

  const handleGenerate = useCallback(async () => {
    if (useBrowser && !prompt.trim()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assetType: selectedAsset,
          prompt,
          useBrowser,
        }),
      });

      const payload = (await response.json()) as JobApiResponse;
      if (!response.ok) {
        console.error(payload.error ?? 'Could not enqueue job.');
        return;
      }

      if (payload.job) {
        upsertJob(payload.job);
        setActiveJobId(payload.job.id);
      }
      await refreshData();
    } catch (error) {
      console.error('Enqueue error:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [prompt, refreshData, selectedAsset, setActiveJobId, upsertJob, useBrowser]);

  const handleCancel = useCallback(
    async (jobId: string) => {
      setActionJobId(jobId);
      try {
        const response = await fetch(`/api/jobs/${jobId}/cancel`, { method: 'POST' });
        const payload = (await response.json()) as JobApiResponse;
        if (!response.ok) {
          console.error(payload.error ?? 'Failed to cancel job.');
          return;
        }
        if (payload.job) {
          upsertJob(payload.job);
        }
        await refreshData();
      } catch (error) {
        console.error('Cancel error:', error);
      } finally {
        setActionJobId(null);
      }
    },
    [refreshData, upsertJob],
  );

  const handleRetry = useCallback(
    async (jobId: string) => {
      setActionJobId(jobId);
      try {
        const response = await fetch(`/api/jobs/${jobId}/retry`, { method: 'POST' });
        const payload = (await response.json()) as JobApiResponse;
        if (!response.ok) {
          console.error(payload.error ?? 'Failed to retry job.');
          return;
        }
        if (payload.job) {
          upsertJob(payload.job);
          setActiveJobId(payload.job.id);
        }
        await refreshData();
      } catch (error) {
        console.error('Retry error:', error);
      } finally {
        setActionJobId(null);
      }
    },
    [refreshData, setActiveJobId, upsertJob],
  );

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white p-8 font-mono">
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-cyan-900/20 blur-[120px] rounded-full" />
      </div>

      <header className="mb-12 border-b border-purple-900/30 pb-6 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">
            TWILIGHT SHADOWPUNK
          </h1>
          <p className="text-cyan-400/60 mt-1 uppercase text-xs tracking-[0.3em]">
            DJ MSQRVVE // ASSET CONTROL PLANE
          </p>
        </div>
        <div className="px-4 py-2 bg-black border border-purple-500/30 rounded flex items-center gap-2">
          {isPolling ? (
            <Loader2 className="animate-spin text-cyan-400" size={14} />
          ) : (
            <Clock3 className="text-cyan-400" size={14} />
          )}
          <span className="text-[10px] text-purple-300 uppercase">
            {isPolling ? 'Refreshing queue...' : 'Queue synced'}
          </span>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <section className="lg:col-span-4 space-y-6">
          <div className="bg-black/40 border border-purple-500/20 p-6 rounded-lg backdrop-blur-md">
            <h2 className="text-xs uppercase text-cyan-400 mb-6 flex items-center gap-2">
              <ChevronRight size={14} /> Queue Controls
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-[10px] text-purple-300/60 uppercase mb-2 ml-1">Asset Type</label>
                <div className="grid grid-cols-1 gap-2">
                  {ASSET_TYPES.map((type) => {
                    const Icon = type.icon;
                    return (
                      <button
                        key={type.id}
                        onClick={() => setSelectedAsset(type.id)}
                        className={cn(
                          'flex items-center gap-3 p-3 rounded text-left transition-all duration-200 border',
                          selectedAsset === type.id
                            ? 'bg-purple-900/30 border-cyan-500/50 text-cyan-400'
                            : 'bg-black/20 border-white/5 text-white/40 hover:border-white/20 hover:text-white',
                        )}
                      >
                        <Icon size={18} />
                        <span className="text-sm font-medium">{type.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-[10px] text-purple-300/60 uppercase mb-2 ml-1">Custom Prompt</label>
                <textarea
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  placeholder="Describe your shadowpunk aesthetic..."
                  className="w-full h-32 bg-black/40 border border-purple-500/20 rounded p-4 text-sm focus:outline-none focus:border-cyan-500/50 transition-colors placeholder:text-white/10"
                />
              </div>

              <div className="flex items-center gap-2 py-2">
                <input
                  type="checkbox"
                  checked={useBrowser}
                  onChange={() => setUseBrowser(!useBrowser)}
                  className="accent-cyan-500"
                />
                <span className="text-[10px] uppercase text-purple-300/60">Use Browser Automation (Free Tokens)</span>
              </div>

              <button
                onClick={() => void handleGenerate()}
                disabled={isGenerateDisabled}
                className={cn(
                  'w-full py-4 rounded font-bold uppercase tracking-widest flex items-center justify-center gap-3 transition-all duration-300',
                  isGenerateDisabled
                    ? 'bg-white/5 text-white/20 cursor-not-allowed'
                    : 'bg-cyan-500 hover:bg-cyan-400 text-black shadow-[0_0_20px_rgba(6,182,212,0.4)]',
                )}
              >
                {isSubmitting ? <Loader2 className="animate-spin" /> : <Zap size={18} />}
                Enqueue Job
              </button>
            </div>
          </div>

          <div className="bg-black/40 border border-purple-500/20 p-6 rounded-lg backdrop-blur-md">
            <h2 className="text-xs uppercase text-cyan-400 mb-4 flex items-center gap-2">
              <ChevronRight size={14} /> Job Queue
            </h2>
            <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
              {jobs.length === 0 ? (
                <p className="text-xs text-white/30">No jobs queued yet.</p>
              ) : (
                jobs.map((job) => (
                  <div
                    key={job.id}
                    className={cn(
                      'border rounded p-3',
                      activeJobId === job.id ? 'border-cyan-500/60 bg-cyan-900/10' : 'border-white/10 bg-black/20',
                    )}
                  >
                    <div className="flex justify-between items-start gap-2">
                      <div>
                        <p className="text-xs uppercase text-white/70">{formatJobTitle(job)}</p>
                        <p className="text-[10px] text-white/30">Created {formatTime(job.createdAt)}</p>
                        {job.queuePosition ? (
                          <p className="text-[10px] text-white/30">Queue position #{job.queuePosition}</p>
                        ) : null}
                      </div>
                      <span className={cn('text-[10px] uppercase px-2 py-1 rounded', STATUS_CLASS[job.status])}>
                        {job.status}
                      </span>
                    </div>

                    <div className="mt-3 flex gap-2">
                      {(job.status === 'queued' || job.status === 'running') && (
                        <button
                          onClick={() => void handleCancel(job.id)}
                          disabled={actionJobId === job.id}
                          className="text-[10px] uppercase px-2 py-1 rounded border border-rose-400/40 text-rose-300 hover:bg-rose-900/20 disabled:opacity-40 flex items-center gap-1"
                        >
                          {actionJobId === job.id ? <Loader2 size={12} className="animate-spin" /> : <XCircle size={12} />}
                          Cancel
                        </button>
                      )}
                      {(job.status === 'failed' || job.status === 'canceled') && (
                        <button
                          onClick={() => void handleRetry(job.id)}
                          disabled={actionJobId === job.id}
                          className="text-[10px] uppercase px-2 py-1 rounded border border-cyan-400/40 text-cyan-300 hover:bg-cyan-900/20 disabled:opacity-40 flex items-center gap-1"
                        >
                          {actionJobId === job.id ? <Loader2 size={12} className="animate-spin" /> : <RotateCcw size={12} />}
                          Retry
                        </button>
                      )}
                    </div>

                    {job.error ? (
                      <p className="mt-2 text-[10px] text-rose-300/80 line-clamp-2">{job.error}</p>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        <section className="lg:col-span-8 space-y-8">
          <div className="bg-black/40 border border-purple-500/20 p-6 rounded-lg backdrop-blur-md min-h-[420px]">
            <h2 className="text-xs uppercase text-cyan-400 mb-6 flex items-center gap-2">
              <ChevronRight size={14} /> Output Gallery
            </h2>

            {successfulJobs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[320px] text-white/10">
                <ImageIcon size={64} className="mb-4 opacity-50" />
                <p className="uppercase tracking-widest text-sm">Waiting for successful output...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {successfulJobs.map((job) => (
                  <div key={job.id} className="bg-black/40 border border-white/5 rounded-lg overflow-hidden group">
                    <div className="aspect-video bg-white/5 relative flex items-center justify-center overflow-hidden">
                      <img
                        src={job.urls[0]}
                        alt={job.prompt}
                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                      />
                    </div>
                    <div className="p-4 border-t border-white/5">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-[10px] text-cyan-400 uppercase tracking-tighter bg-cyan-900/20 px-2 py-0.5 rounded">
                          {formatJobTitle(job)}
                        </span>
                        <span className="text-[10px] text-white/20">{formatTime(job.finishedAt)}</span>
                      </div>
                      <p className="text-xs text-white/60 line-clamp-2 italic">&quot;{job.prompt}&quot;</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-black/40 border border-purple-500/20 p-6 rounded-lg backdrop-blur-md">
            <h2 className="text-xs uppercase text-cyan-400 mb-4 flex items-center gap-2">
              <ChevronRight size={14} /> Ledger History (All Runs)
            </h2>
            <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
              {history.length === 0 ? (
                <p className="text-xs text-white/30">No ledger history found.</p>
              ) : (
                history.map((run) => (
                  <div key={run.runId} className="border border-white/10 bg-black/20 rounded p-3">
                    <div className="flex justify-between items-start gap-2">
                      <div>
                        <p className="text-xs uppercase text-white/70">{run.assetKey.replaceAll('_', ' ')}</p>
                        <p className="text-[10px] text-white/30">Run {run.runId}</p>
                        <p className="text-[10px] text-white/30">Updated {formatTime(run.updatedAt)}</p>
                      </div>
                      <span
                        className={cn(
                          'text-[10px] uppercase px-2 py-1 rounded',
                          run.status === 'success'
                            ? 'bg-emerald-900/40 text-emerald-200'
                            : run.status === 'failed'
                              ? 'bg-rose-900/40 text-rose-200'
                              : run.status === 'running'
                                ? 'bg-amber-900/40 text-amber-200'
                                : 'bg-zinc-800 text-zinc-300',
                        )}
                      >
                        {run.status}
                      </span>
                    </div>
                    {run.error ? <p className="mt-2 text-[10px] text-rose-300/80 line-clamp-2">{run.error}</p> : null}
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
