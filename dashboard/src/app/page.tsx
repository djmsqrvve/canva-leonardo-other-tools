'use client';

import { useState } from 'react';
import { useBrandStore } from './store';
import { 
  Sparkles, 
  Layers, 
  Layout, 
  Zap, 
  ChevronRight, 
  Loader2, 
  Image as ImageIcon,
  Palette
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const ASSET_TYPES = [
  { id: 'social_banner', label: 'Social Banner', icon: Layout },
  { id: 'profile_avatar', label: 'Profile Avatar', icon: Palette },
  { id: 'raid_alert', label: 'Raid Alert', icon: Zap },
  { id: 'helix_tileset', label: 'Helix 2000 Tileset', icon: Layers },
  { id: 'bevy_skybox', label: 'Bevy Skybox', icon: Sparkles },
];

export default function DashboardPage() {
  const { generations, isGenerating, addGeneration, setGenerating, updateGeneration } = useBrandStore();
  const [selectedAsset, setSelectedAsset] = useState(ASSET_TYPES[0].id);
  const [prompt, setPrompt] = useState('');
  const [useBrowser, setUseBrowser] = useState(true);

  const handleGenerate = async () => {
    if (!prompt) return;

    const id = Math.random().toString(36).substr(2, 9);
    const newGen = {
      id,
      type: selectedAsset,
      prompt,
      urls: [],
      status: 'pending' as const,
      timestamp: Date.now()
    };

    addGeneration(newGen);
    setGenerating(true);

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assetType: selectedAsset, prompt, useBrowser }),
      });

      const data = await response.json();
      if (data.urls) {
        updateGeneration(id, { status: 'completed', urls: data.urls });
      } else {
        updateGeneration(id, { status: 'failed' });
      }
    } catch (error) {
      console.error(error);
      updateGeneration(id, { status: 'failed' });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white p-8 font-mono">
      {/* BACKGROUND GLOWS */}
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
            DJ MSQRVVE // ASSET PIPELINE
          </p>
        </div>
        <div className="flex gap-4">
          <div className="px-4 py-2 bg-black border border-purple-500/30 rounded flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_green]" />
            <span className="text-[10px] text-purple-300">SYSTEM ONLINE</span>
          </div>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* LEFT COLUMN: CONTROL PANEL */}
        <section className="lg:col-span-4 space-y-6">
          <div className="bg-black/40 border border-purple-500/20 p-6 rounded-lg backdrop-blur-md shadow-[0_0_20px_rgba(0,0,0,0.5)]">
            <h2 className="text-xs uppercase text-cyan-400 mb-6 flex items-center gap-2">
              <ChevronRight size={14} /> Generator Controls
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
                          "flex items-center gap-3 p-3 rounded text-left transition-all duration-200 border",
                          selectedAsset === type.id 
                            ? "bg-purple-900/30 border-cyan-500/50 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.1)]" 
                            : "bg-black/20 border-white/5 text-white/40 hover:border-white/20 hover:text-white"
                        )}
                      >
                        <Icon size={18} />
                        <span className="text-sm font-medium">{type.label}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <label className="block text-[10px] text-purple-300/60 uppercase mb-2 ml-1">Custom Prompt</label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
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
                onClick={handleGenerate}
                disabled={isGenerating || !prompt}
                className={cn(
                  "w-full py-4 rounded font-bold uppercase tracking-widest flex items-center justify-center gap-3 transition-all duration-300",
                  isGenerating || !prompt
                    ? "bg-white/5 text-white/20 cursor-not-allowed"
                    : "bg-cyan-500 hover:bg-cyan-400 text-black shadow-[0_0_20px_rgba(6,182,212,0.4)]"
                )}
              >
                {isGenerating ? <Loader2 className="animate-spin" /> : <Zap size={18} />}
                Generate Asset
              </button>
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN: GALLERY */}
        <section className="lg:col-span-8">
          <div className="bg-black/40 border border-purple-500/20 p-6 rounded-lg backdrop-blur-md min-h-[600px]">
            <h2 className="text-xs uppercase text-cyan-400 mb-6 flex items-center gap-2">
              <ChevronRight size={14} /> Output Gallery
            </h2>

            {generations.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[500px] text-white/10">
                <ImageIcon size={64} className="mb-4 opacity-50" />
                <p className="uppercase tracking-widest text-sm">Waiting for incoming signal...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {generations.map((gen) => (
                  <div key={gen.id} className="bg-black/40 border border-white/5 rounded-lg overflow-hidden group">
                    <div className="aspect-video bg-white/5 relative flex items-center justify-center overflow-hidden">
                      {gen.status === 'pending' ? (
                        <div className="flex flex-col items-center gap-2">
                          <Loader2 className="animate-spin text-cyan-500" size={32} />
                          <span className="text-[10px] text-cyan-400 animate-pulse uppercase">Processing...</span>
                        </div>
                      ) : gen.status === 'completed' ? (
                        <img 
                          src={gen.urls[0]} 
                          alt={gen.prompt} 
                          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                        />
                      ) : (
                        <span className="text-red-500 text-xs uppercase">Generation Failed</span>
                      )}
                    </div>
                    <div className="p-4 border-t border-white/5">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-[10px] text-cyan-400 uppercase tracking-tighter bg-cyan-900/20 px-2 py-0.5 rounded">
                          {gen.type.replace('_', ' ')}
                        </span>
                        <span className="text-[10px] text-white/20">
                          {new Date(gen.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-xs text-white/60 line-clamp-2 italic">"{gen.prompt}"</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
