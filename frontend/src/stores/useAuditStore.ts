import { create } from "zustand";
import type { AuditIngestResponse } from "@/types/audit";
import { ingestDocument } from "@/lib/auditApi";

interface AuditStore {
  file: File | null;
  isLoading: boolean;
  result: AuditIngestResponse | null;
  error: string | null;
  setFile: (file: File | null) => void;
  ingest: () => Promise<void>;
  reset: () => void;
}

export const useAuditStore = create<AuditStore>((set, get) => ({
  file: null,
  isLoading: false,
  result: null,
  error: null,

  setFile: (file) => set({ file, result: null, error: null }),

  ingest: async () => {
    const { file } = get();
    if (!file) return;
    set({ isLoading: true, error: null });
    try {
      const result = await ingestDocument(file);
      set({ result, isLoading: false });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  reset: () => set({ file: null, isLoading: false, result: null, error: null }),
}));
