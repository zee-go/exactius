"use client";

import { useRouter } from "next/navigation";
import { useWizardStore } from "@/lib/store/wizardStore";
import { WizardProgress } from "./WizardProgress";
import { StepAccount } from "./StepAccount";
import { StepCampaignType } from "./StepCampaignType";
import { StepDriveUrl } from "./StepDriveUrl";
import { StepContext } from "./StepContext";
import { StepPreview } from "./StepPreview";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, History } from "lucide-react";

const STEP_TITLES = [
  { title: "Select Account", description: "Choose the client ad account for this campaign" },
  { title: "Campaign Type", description: "Select the type of campaign to create" },
  { title: "Drive Assets", description: "Link the Google Drive folder with your creative assets" },
  { title: "Campaign Details", description: "Set product name, audience, and budget" },
  { title: "Preview & Launch", description: "Review everything before launching" },
];

export function CampaignWizard() {
  const router = useRouter();
  const { step, nextStep, prevStep, launchData, reset } = useWizardStore();

  // Success state after launch
  if (launchData?.data.success) {
    const data = launchData.data;
    return (
      <Card className="max-w-2xl mx-auto">
        <CardContent className="pt-8 pb-8 text-center space-y-4">
          <div className="flex justify-center">
            <CheckCircle2 className="h-16 w-16 text-green-500" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Campaign Launched!</h2>
            <p className="text-muted-foreground mt-1">
              Your campaign has been created and is ready for review in Meta Ads Manager.
            </p>
          </div>
          <div className="rounded-lg border bg-muted/40 p-4 text-left space-y-2 text-sm">
            {data.campaign_id && (
              <div className="flex gap-2">
                <span className="text-muted-foreground w-24">Campaign ID</span>
                <code className="font-mono text-xs">{data.campaign_id}</code>
              </div>
            )}
            {data.adset_id && (
              <div className="flex gap-2">
                <span className="text-muted-foreground w-24">Ad Set ID</span>
                <code className="font-mono text-xs">{data.adset_id}</code>
              </div>
            )}
            <div className="flex gap-2">
              <span className="text-muted-foreground w-24">Ads Created</span>
              <span className="font-medium">{data.ad_ids.length}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-muted-foreground w-24">Status</span>
              <span className="font-medium text-yellow-600">PAUSED — Review in Ads Manager</span>
            </div>
          </div>
          <div className="flex gap-3 justify-center pt-2">
            <Button
              variant="outline"
              onClick={() => router.push("/campaigns/history")}
              className="gap-2"
            >
              <History className="h-4 w-4" />
              View History
            </Button>
            <Button
              onClick={() => {
                reset();
                router.push("/campaigns/create");
              }}
            >
              Create Another
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { title, description } = STEP_TITLES[step - 1];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Progress indicator */}
      <div className="flex justify-center">
        <WizardProgress currentStep={step} />
      </div>

      {/* Step card */}
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          {step === 1 && <StepAccount onNext={nextStep} />}
          {step === 2 && <StepCampaignType onNext={nextStep} onBack={prevStep} />}
          {step === 3 && <StepDriveUrl onNext={nextStep} onBack={prevStep} />}
          {step === 4 && <StepContext onNext={nextStep} onBack={prevStep} />}
          {step === 5 && (
            <StepPreview
              onBack={prevStep}
              onLaunched={() => {}} // launchData triggers success view above
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
