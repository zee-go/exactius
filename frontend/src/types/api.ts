/**
 * TypeScript types mirroring backend Pydantic models
 */

// Account types
export interface AccountInfo {
  id: string;
  name: string;
  display_name: string;
}

export interface AccountListResponse {
  accounts: AccountInfo[];
  count: number;
}

export interface NamingRule {
  campaign?: string;
  adset?: string;
  ad?: string;
}

export interface AccountDetail {
  account_id: string;
  account_name: string;
  display_name: string;
  campaign_types: string[];
  naming_rules: Record<string, NamingRule>;
  defaults?: Record<string, any>;
  meta?: Record<string, string>;
}

// Campaign types
export interface CampaignLaunchRequest {
  account_id: string;
  campaign_type: string;
  drive_url: string;
  context: Record<string, any>;
  preview_only?: boolean;
}

export interface DriveAsset {
  file_id: string;
  name: string;
  mime_type: string;
  size: number;
  local_path?: string;
}

export interface LaunchResult {
  success: boolean;
  campaign_id?: string;
  adset_id?: string;
  ad_ids: string[];
  creative_ids: string[];
  errors: string[];
  warnings: string[];
  metadata: {
    names?: {
      campaign: string;
      adset: string;
      ad: string;
    };
    asset_count?: number;
    valid_asset_count?: number;
    assets?: DriveAsset[];
    preview?: boolean;
  };
}

export interface CampaignLaunchResponse {
  status: "success" | "error";
  preview_only?: boolean;
  data: LaunchResult;
  errors?: string[];
  warnings?: string[];
}

// Validation response
export interface ValidationResponse {
  status: "valid" | "invalid";
  message?: string;
}

// Campaign types list response
export interface CampaignTypesResponse {
  campaign_types: string[];
}
