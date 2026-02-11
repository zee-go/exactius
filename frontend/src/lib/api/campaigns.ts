/**
 * Campaign API endpoints
 */
import { apiClient } from "./client";
import type { CampaignLaunchRequest, CampaignLaunchResponse } from "@/types/api";

export const campaignsApi = {
  /**
   * Preview campaign without creating (dry-run)
   */
  preview: (data: CampaignLaunchRequest) =>
    apiClient.post<CampaignLaunchResponse>("/api/campaigns/preview", {
      ...data,
      preview_only: true,
    }),

  /**
   * Launch campaign from Drive assets
   */
  launch: (data: CampaignLaunchRequest) =>
    apiClient.post<CampaignLaunchResponse>("/api/campaigns/launch", data),
};
