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
    if (!formData.graphFile || !formData.format || !formData.protectedAttr || !formData.predictionSource) {
      set({ error: "Missing required fields" });
      return;
    }
    
    set({ isLoading: true, error: null });
    try {
      const result = await analyzeGraphModel(formData as GraphModelAuditPayload);
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
