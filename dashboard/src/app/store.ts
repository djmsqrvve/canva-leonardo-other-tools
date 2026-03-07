import { create } from 'zustand';

interface Generation {
  id: string;
  type: string;
  prompt: string;
  urls: string[];
  status: 'pending' | 'completed' | 'failed';
  timestamp: number;
}

interface BrandStore {
  generations: Generation[];
  isGenerating: boolean;
  addGeneration: (gen: Generation) => void;
  updateGeneration: (id: string, updates: Partial<Generation>) => void;
  setGenerating: (val: boolean) => void;
}

export const useBrandStore = create<BrandStore>((set) => ({
  generations: [],
  isGenerating: false,
  addGeneration: (gen) => set((state) => ({ generations: [gen, ...state.generations] })),
  updateGeneration: (id, updates) =>
    set((state) => ({
      generations: state.generations.map((gen) =>
        gen.id === id ? { ...gen, ...updates } : gen
      ),
    })),
  setGenerating: (val) => set({ isGenerating: val }),
}));
