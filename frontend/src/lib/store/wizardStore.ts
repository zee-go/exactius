import { create } from "zustand";
import type { CampaignLaunchResponse } from "@/types/api";

export const WIZARD_STEPS = [
  { id: 1, label: "Account" },
  { id: 2, label: "Campaign Type" },
  { id: 3, label: "Drive URL" },
  { id: 4, label: "Details" },
  { id: 5, label: "Preview & Launch" },
] as const;

export const TOTAL_STEPS = WIZARD_STEPS.length;

export interface WizardContext {
  product: string;
  audience_type: string;
  daily_budget: number;
  [key: string]: string | number;
}

interface WizardState {
  step: number;
  accountId: string;
  accountDisplayName: string;
  campaignType: string;
  driveUrl: string;
  context: WizardContext;
  previewData: CampaignLaunchResponse | null;
  launchData: CampaignLaunchResponse | null;

  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  setAccount: (id: string, displayName: string) => void;
  setCampaignType: (type: string) => void;
  setDriveUrl: (url: string) => void;
  setContext: (context: WizardContext) => void;
  setPreviewData: (data: CampaignLaunchResponse | null) => void;
  setLaunchData: (data: CampaignLaunchResponse | null) => void;
  reset: () => void;
}

const defaultContext: WizardContext = {
  product: "",
  audience_type: "Broad",
  daily_budget: 1000,
};

export const useWizardStore = create<WizardState>((set, get) => ({
  step: 1,
  accountId: "",
  accountDisplayName: "",
  campaignType: "",
  driveUrl: "",
  context: defaultContext,
  previewData: null,
  launchData: null,

  setStep: (step) => set({ step }),
  nextStep: () => set({ step: Math.min(get().step + 1, TOTAL_STEPS) }),
  prevStep: () => set({ step: Math.max(get().step - 1, 1) }),

  setAccount: (id, displayName) =>
    set({ accountId: id, accountDisplayName: displayName, campaignType: "", previewData: null }),

  setCampaignType: (type) =>
    set({ campaignType: type, previewData: null }),

  setDriveUrl: (url) =>
    set({ driveUrl: url, previewData: null }),

  setContext: (context) =>
    set({ context, previewData: null }),

  setPreviewData: (data) => set({ previewData: data }),
  setLaunchData: (data) => set({ launchData: data }),

  reset: () =>
    set({
      step: 1,
      accountId: "",
      accountDisplayName: "",
      campaignType: "",
      driveUrl: "",
      context: defaultContext,
      previewData: null,
      launchData: null,
    }),
}));
