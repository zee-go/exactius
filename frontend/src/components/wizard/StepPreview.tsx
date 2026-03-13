"use client";

import { useEffect } from "react";
import { useWizardStore } from "@/lib/store/wizardStore";
import { useHistoryStore } from "@/lib/store/historyStore";
import { useCampaignPreview, useCampaignLaunch } from "@/lib/hooks/useCampaigns";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  FileImage,
  Tag,
  TriangleAlert,
  Rocket,
} from "lucide-react";

interface StepPreviewProps {
  onBack: () => void;
  onLaunched: () => void;
}

export function StepPreview({ onBack, onLaunched }: StepPreviewProps) {
  const { accountId, accountDisplayName, campaignType, driveUrl, context, previewData, setPreviewData, setLaunchData } =
    useWizardStore();
  const addEntry = useHistoryStore((s) => s.addEntry);

  const previewMutation = useCampaignPreview();
  const launchMutation = useCampaignLaunch();

  // Auto-run preview on mount
  useEffect(() => {
    if (!previewData) {
      previewMutation.mutate(
        {
          account_id: accountId,
          campaign_type: campaignType,
          drive_url: driveUrl,
          context: { ...context },
          preview_only: true,
        },
        {
          onSuccess: (data) => setPreviewData(data),
        }
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLaunch = () => {
    launchMutation.mutate(
      {
        account_id: accountId,
        campaign_type: campaignType,
        drive_url: driveUrl,
        context: { ...context },
        preview_only: false,
      },
      {
        onSuccess: (data) => {
          setLaunchData(data);
          addEntry({
            accountId,
            accountDisplayName,
            campaignType,
            campaignId: data.data.campaign_id,
            adsetId: data.data.adset_id,
            adCount: data.data.ad_ids.length,
            status: data.data.success ? "success" : "error",
            names: data.data.metadata?.names,
            errors: data.data.errors,
          });
          onLaunched();
        },
      }
    );
  };

  // Loading state
  if (previewMutation.isPending && !previewData) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-24 w-full rounded-lg" />
        <Skeleton className="h-24 w-full rounded-lg" />
      </div>
    );
  }

  // Preview error
  if (previewMutation.isError && !previewData) {
    return (
      <div className="space-y-4">
        <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0" />
          <div>
            <p className="font-medium">Preview failed</p>
            <p className="mt-1 text-sm">
              {previewMutation.error instanceof Error
                ? previewMutation.error.message
                : "Could not connect to API server"}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onBack} className="flex-1">
            Back
          </Button>
          <Button
            onClick={() =>
              previewMutation.mutate(
                { account_id: accountId, campaign_type: campaignType, drive_url: driveUrl, context: { ...context }, preview_only: true },
                { onSuccess: (data) => setPreviewData(data) }
              )
            }
            className="flex-1"
          >
            Retry Preview
          </Button>
        </div>
      </div>
    );
  }

  const preview = previewData?.data;
  const names = preview?.metadata?.names;
  const assetCount = preview?.metadata?.valid_asset_count ?? preview?.metadata?.asset_count ?? 0;
  const warnings = preview?.warnings ?? [];

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Campaign Summary
        </h3>

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground w-24 flex-shrink-0">Account</span>
            <span className="font-medium">{accountDisplayName}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground w-24 flex-shrink-0">Type</span>
            <span className="font-medium">{campaignType.replace(/_/g, " ")}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground w-24 flex-shrink-0">Product</span>
            <span className="font-medium">{context.product}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground w-24 flex-shrink-0">Budget</span>
            <span className="font-medium">${(context.daily_budget / 100).toFixed(2)}/day</span>
          </div>
        </div>
      </div>

      {/* Asset count */}
      {assetCount > 0 && (
        <div className="flex items-center gap-2 rounded-lg border bg-muted/40 px-4 py-3">
          <FileImage className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">
            <span className="font-medium">{assetCount}</span> valid asset
            {assetCount !== 1 ? "s" : ""} found
          </span>
        </div>
      )}

      {/* Generated names */}
      {names && (
        <div className="space-y-2 rounded-lg border p-4">
          <div className="flex items-center gap-1.5 text-sm font-medium">
            <Tag className="h-3.5 w-3.5" />
            Generated Names
          </div>
          <div className="space-y-1 text-sm">
            <div className="flex gap-2">
              <span className="text-muted-foreground w-16 flex-shrink-0">Campaign</span>
              <code className="text-xs bg-muted rounded px-1.5 py-0.5 break-all">{names.campaign}</code>
            </div>
            <div className="flex gap-2">
              <span className="text-muted-foreground w-16 flex-shrink-0">Ad Set</span>
              <code className="text-xs bg-muted rounded px-1.5 py-0.5 break-all">{names.adset}</code>
            </div>
            <div className="flex gap-2">
              <span className="text-muted-foreground w-16 flex-shrink-0">Ad</span>
              <code className="text-xs bg-muted rounded px-1.5 py-0.5 break-all">{names.ad}</code>
            </div>
          </div>
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="space-y-1 rounded-lg border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-900 dark:bg-yellow-950">
          <div className="flex items-center gap-1.5 text-sm font-medium text-yellow-800 dark:text-yellow-200">
            <TriangleAlert className="h-4 w-4" />
            {warnings.length} warning{warnings.length !== 1 ? "s" : ""}
          </div>
          <ul className="space-y-0.5 pl-5 text-xs text-yellow-700 dark:text-yellow-300 list-disc">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Preview errors */}
      {preview?.errors && preview.errors.length > 0 && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive text-sm">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <ul className="space-y-0.5 list-disc pl-4">
            {preview.errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Launch confirmation */}
      {preview?.success && (
        <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          Campaign will start <strong className="mx-1">PAUSED</strong> for your review before any spend.
        </div>
      )}

      {/* Launch error */}
      {launchMutation.isError && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>
            {launchMutation.error instanceof Error
              ? launchMutation.error.message
              : "Launch failed. Please try again."}
          </span>
        </div>
      )}

      <div className="flex gap-2 pt-2">
        <Button
          variant="outline"
          onClick={onBack}
          disabled={launchMutation.isPending}
          className="flex-1"
        >
          Back
        </Button>
        <Button
          onClick={handleLaunch}
          disabled={!preview?.success || launchMutation.isPending}
          className="flex-1 gap-2"
        >
          {launchMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Launching...
            </>
          ) : (
            <>
              <Rocket className="h-4 w-4" />
              Launch Campaign
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
