/**
 * React Query hooks for account management
 */
import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { accountsApi } from "@/lib/api";
import type { AccountListResponse, AccountDetail, CampaignTypesResponse } from "@/types/api";

/**
 * Fetch all accounts
 */
export function useAccounts(): UseQueryResult<AccountListResponse> {
  return useQuery({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.listAccounts(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 2,
  });
}

/**
 * Fetch single account details
 */
export function useAccount(accountId: string): UseQueryResult<AccountDetail> {
  return useQuery({
    queryKey: ["accounts", accountId],
    queryFn: () => accountsApi.getAccount(accountId),
    enabled: !!accountId, // Only fetch if accountId is provided
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Fetch available campaign types for an account
 */
export function useCampaignTypes(accountId: string): UseQueryResult<CampaignTypesResponse> {
  return useQuery({
    queryKey: ["accounts", accountId, "campaign-types"],
    queryFn: () => accountsApi.getCampaignTypes(accountId),
    enabled: !!accountId,
    staleTime: 10 * 60 * 1000, // Campaign types rarely change
    retry: 2,
  });
}

/**
 * Validate account credentials
 */
export function useAccountValidation(accountId: string) {
  return useQuery({
    queryKey: ["accounts", accountId, "validate"],
    queryFn: () => accountsApi.validateAccount(accountId),
    enabled: !!accountId,
    staleTime: 1 * 60 * 1000, // Revalidate more frequently
    retry: 1,
  });
}
