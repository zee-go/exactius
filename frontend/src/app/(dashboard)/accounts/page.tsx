"use client";

import { useAccounts } from "@/lib/hooks/useAccounts";
import { AccountCard } from "@/components/accounts/AccountCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export default function AccountsPage() {
  const { data, isLoading, error } = useAccounts();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error Loading Accounts</CardTitle>
          <CardDescription>
            {error instanceof Error ? error.message : "Failed to load accounts"}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!data || data.count === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Accounts Found</CardTitle>
          <CardDescription>
            No client accounts have been configured yet. Please configure accounts in Google Secret
            Manager.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Client Accounts</h1>
        <p className="text-muted-foreground">
          Manage and launch campaigns for your client accounts
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data.accounts.map((account) => (
          <AccountCard key={account.id} account={account} />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Account Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            <p>Total Accounts: {data.count}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
