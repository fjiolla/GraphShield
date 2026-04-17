import { create } from "zustand";
import type { StructModelAuditResponse } from "@/types/fairness";
import { uploadAndAudit } from "@/lib/modelAuditApi";

interface ModelAuditStore {
  modelFile: File | null;
  datasetFile: File | null;
  isLoading: boolean;
  result: StructModelAuditResponse | null;
  error: string | null;

  setModelFile: (file: File | null) => void;
  setDatasetFile: (file: File | null) => void;
  runAudit: () => Promise<void>;
  reset: () => void;
}

export const useModelAuditStore = create<ModelAuditStore>((set, get) => ({
  modelFile: null,
  datasetFile: null,
  isLoading: false,
  result: null,
  error: null,

  setModelFile: (file) => set({ modelFile: file, result: null, error: null }),
  setDatasetFile: (file) => set({ datasetFile: file, result: null, error: null }),

  runAudit: async () => {
    const { modelFile, datasetFile } = get();
    if (!modelFile || !datasetFile) {
      set({ error: "Please provide both model and dataset files" });
      return;
    }

    set({ isLoading: true, error: null });
    try {
      const result = await uploadAndAudit(modelFile, datasetFile);
      set({ result, isLoading: false });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  reset: () => set({
    modelFile: null,
    datasetFile: null,
    isLoading: false,
    result: null,
    error: null,
  })
}));
