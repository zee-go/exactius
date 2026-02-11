/**
 * React Query hooks for campaign management
 */
import { useMutation, useQueryClient, UseMutationResult } from "@tanstack/react-query";
import { campaignsApi } from "@/lib/api";
import type { CampaignLaunchRequest, CampaignLaunchResponse } from "@/types/api";
import { handleApiError } from "@/lib/utils/errorHandler";

/**
 * Preview campaign without creating (dry-run)
 */
export function useCampaignPreview(): UseMutationResult<
  CampaignLaunchResponse,
  Error,
  CampaignLaunchRequest
> {
  return useMutation({
    mutationFn: (data: CampaignLaunchRequest) => campaignsApi.preview(data),
    onError: (error) => {
      console.error("Campaign preview failed:", handleApiError(error));
    },
  });
}

/**
 * Launch campaign from Drive assets
 */
export function useCampaignLaunch(): UseMutationResult<
  CampaignLaunchResponse,
  Error,
  CampaignLaunchRequest
> {
  const _queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CampaignLaunchRequest) => campaignsApi.launch(data),
    onSuccess: (result, _variables) => {
      console.log("Campaign launched successfully:", result);

      // Invalidate relevant queries to refetch fresh data
      if (result.data.campaign_id) {
        // Future: invalidate campaign history query when implemented
        // _queryClient.invalidateQueries({ queryKey: ['campaign-history'] });
      }
    },
    onError: (error) => {
      console.error("Campaign launch failed:", handleApiError(error));
    },
  });
}
