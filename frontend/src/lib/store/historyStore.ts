import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface HistoryEntry {
  id: string;
  timestamp: string;
  accountId: string;
  accountDisplayName: string;
  campaignType: string;
  campaignId?: string;
  adsetId?: string;
  adCount: number;
  status: "success" | "error";
  names?: {
    campaign: string;
    adset: string;
    ad: string;
  };
  errors?: string[];
}

interface HistoryState {
  entries: HistoryEntry[];
  addEntry: (entry: Omit<HistoryEntry, "id" | "timestamp">) => void;
  clearHistory: () => void;
}

export const useHistoryStore = create<HistoryState>()(
  persist(
    (set) => ({
      entries: [],

      addEntry: (entry) =>
        set((state) => ({
          entries: [
            {
              ...entry,
              id: crypto.randomUUID(),
              timestamp: new Date().toISOString(),
            },
            ...state.entries,
          ].slice(0, 100), // keep last 100 entries
        })),

      clearHistory: () => set({ entries: [] }),
    }),
    {
      name: "exactius-campaign-history",
    }
  )
);
