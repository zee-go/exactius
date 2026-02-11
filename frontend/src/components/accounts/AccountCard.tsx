"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, AlertCircle, PlusCircle, Eye } from "lucide-react";
import Link from "next/link";
import type { AccountInfo } from "@/types/api";

interface AccountCardProps {
  account: AccountInfo;
  validationStatus?: "valid" | "invalid" | "unknown";
}

export function AccountCard({ account, validationStatus = "unknown" }: AccountCardProps) {
  const getStatusBadge = () => {
    switch (validationStatus) {
      case "valid":
        return (
          <Badge variant="default" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            Valid
          </Badge>
        );
      case "invalid":
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Invalid
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className="gap-1">
            Unknown
          </Badge>
        );
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>{account.display_name}</CardTitle>
            <CardDescription>{account.id}</CardDescription>
          </div>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Link href={`/accounts/${account.id}`} className="flex-1">
            <Button variant="outline" className="w-full gap-2">
              <Eye className="h-4 w-4" />
              View Details
            </Button>
          </Link>
          <Link
            href={`/campaigns/create?account=${account.id}`}
            className="flex-1"
          >
            <Button className="w-full gap-2">
              <PlusCircle className="h-4 w-4" />
              Create Campaign
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
