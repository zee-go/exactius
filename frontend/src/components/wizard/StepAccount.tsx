"use client";

import { useAccounts } from "@/lib/hooks/useAccounts";
import { useWizardStore } from "@/lib/store/wizardStore";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle } from "lucide-react";

interface StepAccountProps {
  onNext: () => void;
}

export function StepAccount({ onNext }: StepAccountProps) {
  const { data, isLoading, error } = useAccounts();
  const { accountId, setAccount } = useWizardStore();

  const handleSelect = (id: string, displayName: string) => {
    setAccount(id, displayName);
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        <AlertCircle className="h-5 w-5 flex-shrink-0" />
        <p className="text-sm">Failed to load accounts. Make sure the API server is running.</p>
      </div>
    );
  }

  if (!data || data.count === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        <p className="font-medium">No accounts configured</p>
        <p className="mt-1 text-sm">Add client accounts to Google Secret Manager first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        {data.accounts.map((account) => {
          const isSelected = accountId === account.id;
          return (
            <button
              key={account.id}
              onClick={() => handleSelect(account.id, account.display_name)}
              className={cn(
                "flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:bg-accent",
                isSelected && "border-primary bg-primary/5"
              )}
            >
              <div>
                <p className="font-medium">{account.display_name}</p>
                <p className="text-sm text-muted-foreground">{account.id}</p>
              </div>
              {isSelected && <CheckCircle2 className="h-5 w-5 text-primary" />}
            </button>
          );
        })}
      </div>

      <Button onClick={onNext} disabled={!accountId} className="w-full">
        Continue
      </Button>
    </div>
  );
}
