"use client";

import { useCampaignTypes } from "@/lib/hooks/useAccounts";
import { useWizardStore } from "@/lib/store/wizardStore";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle } from "lucide-react";

interface StepCampaignTypeProps {
  onNext: () => void;
  onBack: () => void;
}

export function StepCampaignType({ onNext, onBack }: StepCampaignTypeProps) {
  const { accountId, campaignType, setCampaignType } = useWizardStore();
  const { data, isLoading, error } = useCampaignTypes(accountId);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        <AlertCircle className="h-5 w-5 flex-shrink-0" />
        <p className="text-sm">Failed to load campaign types for this account.</p>
      </div>
    );
  }

  const types = data?.campaign_types ?? [];

  if (types.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        <p className="font-medium">No campaign types configured</p>
        <p className="mt-1 text-sm">This account has no naming rules defined.</p>
      </div>
    );
  }

  const formatLabel = (type: string) =>
    type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        {types.map((type) => {
          const isSelected = campaignType === type;
          return (
            <button
              key={type}
              onClick={() => setCampaignType(type)}
              className={cn(
                "flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:bg-accent",
                isSelected && "border-primary bg-primary/5"
              )}
            >
              <div>
                <p className="font-medium">{formatLabel(type)}</p>
                <p className="font-mono text-xs text-muted-foreground">{type}</p>
              </div>
              {isSelected && <CheckCircle2 className="h-5 w-5 text-primary" />}
            </button>
          );
        })}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button onClick={onNext} disabled={!campaignType} className="flex-1">
          Continue
        </Button>
      </div>
    </div>
  );
}
