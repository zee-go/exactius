/**
 * Account API endpoints
 */
import { apiClient } from "./client";
import type {
  AccountListResponse,
  AccountDetail,
  ValidationResponse,
  CampaignTypesResponse,
} from "@/types/api";

export const accountsApi = {
  /**
   * List all configured accounts
   */
  listAccounts: () => apiClient.get<AccountListResponse>("/api/accounts/"),

  /**
   * Get detailed account information
   */
  getAccount: (id: string) => apiClient.get<AccountDetail>(`/api/accounts/${id}`),

  /**
   * Validate account credentials
   */
  validateAccount: (id: string) =>
    apiClient.get<ValidationResponse>(`/api/accounts/${id}/validate`),

  /**
   * Get available campaign types for account
   */
  getCampaignTypes: (id: string) =>
    apiClient.get<CampaignTypesResponse>(`/api/accounts/${id}/campaign-types`),
};
