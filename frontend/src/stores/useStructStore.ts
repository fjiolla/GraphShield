import { create } from "zustand";
import type { StructUploadResponse, StructRunAuditResponse, StructReportResponse } from "@/types/fairness";
import { uploadDataset, runAudit, getReport, listTables } from "@/lib/structAuditApi";

interface StructStore {
  uploadFile: File | null;
  uploadResult: StructUploadResponse | null;
  isUploading: boolean;
  
  isAuditing: boolean;
  runAuditResult: StructRunAuditResponse | null;
  
  report: StructReportResponse | null;
  isFetchingReport: boolean;
  
  tables: string[];
  
  error: string | null;

  setUploadFile: (file: File | null) => void;
  upload: () => Promise<void>;
  startAudit: () => Promise<void>;
  fetchReport: () => Promise<void>;
  loadTables: () => Promise<void>;
  reset: () => void;
}

export const useStructStore = create<StructStore>((set, get) => ({
  uploadFile: null,
  uploadResult: null,
  isUploading: false,
  
  isAuditing: false,
  runAuditResult: null,
  
  report: null,
  isFetchingReport: false,
  
  tables: [],
  error: null,

  setUploadFile: (file) => set({ uploadFile: file, error: null }),

  upload: async () => {
    const { uploadFile } = get();
    if (!uploadFile) return;
    set({ isUploading: true, error: null });
    try {
      const result = await uploadDataset(uploadFile);
      set({ uploadResult: result, isUploading: false });
      get().loadTables(); // Reload tables list
    } catch (e) {
      set({ error: (e as Error).message, isUploading: false });
    }
  },

  startAudit: async () => {
    set({ isAuditing: true, error: null });
    try {
      const result = await runAudit();
      set({ runAuditResult: result, isAuditing: false });
    } catch (e) {
      set({ error: (e as Error).message, isAuditing: false });
    }
  },

  fetchReport: async () => {
    set({ isFetchingReport: true, error: null });
    try {
      const report = await getReport();
      set({ report, isFetchingReport: false });
    } catch (e) {
      set({ error: (e as Error).message, isFetchingReport: false });
    }
  },
  
  loadTables: async () => {
    try {
      const { tables } = await listTables();
      set({ tables });
    } catch (e) {
      console.error("Failed to load tables", e);
    }
  },

  reset: () => set({
    uploadFile: null,
    uploadResult: null,
    isUploading: false,
    isAuditing: false,
    runAuditResult: null,
    report: null,
    isFetchingReport: false,
    error: null
  })
}));
