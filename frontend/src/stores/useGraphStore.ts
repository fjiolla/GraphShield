import { create } from "zustand";
import type { GraphAnalysisResult } from "@/types/graph";
import { analyzeGraphBias } from "@/lib/graphApi";

interface GraphStore {
  graphFile: File | null;
  nodesFile: File | null;
  config: string;
  isLoading: boolean;
  result: GraphAnalysisResult | null;
  error: string | null;
  
  setGraphFile: (file: File | null) => void;
  setNodesFile: (file: File | null) => void;
  setConfig: (config: string) => void;
  
  analyze: () => Promise<void>;
  reset: () => void;
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  graphFile: null,
  nodesFile: null,
  config: "",
  isLoading: false,
  result: null,
  error: null,

  setGraphFile: (graphFile) => set({ graphFile, result: null, error: null }),
  setNodesFile: (nodesFile) => set({ nodesFile }),
  setConfig: (config) => set({ config }),

  analyze: async () => {
    const { graphFile, nodesFile, config } = get();
    if (!graphFile) return;
    
    set({ isLoading: true, error: null });
    try {
      let parsedConfig;
      if (config.trim()) {
        try {
          parsedConfig = JSON.parse(config);
        } catch {
          throw new Error("Invalid JSON in config override");
        }
      }
      
      const result = await analyzeGraphBias(graphFile, nodesFile || undefined, parsedConfig);
      set({ result, isLoading: false });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  reset: () => set({ 
    graphFile: null, 
    nodesFile: null, 
    config: "", 
    isLoading: false, 
    result: null, 
    error: null 
  }),
}));
