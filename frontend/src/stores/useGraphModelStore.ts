import { create } from "zustand";
import type { GraphModelAuditResult } from "@/types/graph";
import { analyzeGraphModel, type GraphModelAuditPayload } from "@/lib/graphModelApi";

interface GraphModelStore {
  formData: Partial<GraphModelAuditPayload>;
  isLoading: boolean;
  result: GraphModelAuditResult | null;
  error: string | null;
  
  updateFormData: (data: Partial<GraphModelAuditPayload>) => void;
  analyze: () => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useGraphModelStore = create<GraphModelStore>((set, get) => ({
  formData: {},
  isLoading: false,
  result: null,
  error: null,

  updateFormData: (data) => set((state) => ({ 
    formData: { ...state.formData, ...data },
    result: null,
    error: null
  })),

  analyze: async () => {
    const { formData } = get();
    if (!formData.graphFile || !formData.format) {
      set({ error: "Please upload a graph file and select its format." });
      return;
    }

    // Default predictionSource to "embedded" if user never touched the dropdown
    const payload: GraphModelAuditPayload = {
      ...formData as GraphModelAuditPayload,
      predictionSource: formData.predictionSource ?? "embedded",
    };
    
    set({ isLoading: true, error: null });
    try {
      const result = await analyzeGraphModel(payload);
      set({ result, isLoading: false });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),

  reset: () => set({ 
    formData: {},
    isLoading: false, 
    result: null, 
    error: null 
  }),
}));
