"use client";

import { useHistoryStore } from "@/lib/store/historyStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CheckCircle2, AlertCircle, Trash2, PlusCircle } from "lucide-react";
import Link from "next/link";
import { format } from "date-fns";

export default function HistoryPage() {
  const { entries, clearHistory } = useHistoryStore();

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">Campaign History</h1>
          <p className="text-muted-foreground">
            Campaigns launched in this browser session
          </p>
        </div>
        <div className="flex gap-2">
          {entries.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={clearHistory}
              className="gap-2 text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
              Clear History
            </Button>
          )}
          <Link href="/campaigns/create">
            <Button size="sm" className="gap-2">
              <PlusCircle className="h-4 w-4" />
              New Campaign
            </Button>
          </Link>
        </div>
      </div>

      {entries.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No campaigns yet</CardTitle>
            <CardDescription>
              Campaigns you launch will appear here. History is stored in your browser.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/campaigns/create">
              <Button>Create Your First Campaign</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Campaign Name</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Ads</TableHead>
                  <TableHead>Launched</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>
                      {entry.status === "success" ? (
                        <Badge variant="default" className="gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Success
                        </Badge>
                      ) : (
                        <Badge variant="destructive" className="gap-1">
                          <AlertCircle className="h-3 w-3" />
                          Failed
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm">
                          {entry.names?.campaign ?? entry.campaignId ?? "—"}
                        </p>
                        {entry.campaignId && (
                          <p className="font-mono text-xs text-muted-foreground">
                            {entry.campaignId}
                          </p>
                        )}
                        {entry.errors && entry.errors.length > 0 && (
                          <p className="text-xs text-destructive mt-0.5">
                            {entry.errors[0]}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">{entry.accountDisplayName}</TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {entry.campaignType.replace(/_/g, " ")}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">{entry.adCount}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(new Date(entry.timestamp), "MMM d, yyyy HH:mm")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
