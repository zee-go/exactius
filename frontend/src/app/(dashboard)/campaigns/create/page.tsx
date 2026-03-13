import { CampaignWizard } from "@/components/wizard/CampaignWizard";

export default function CreateCampaignPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Create Campaign</h1>
        <p className="text-muted-foreground">
          Launch a Meta ad campaign from your Google Drive assets
        </p>
      </div>
      <CampaignWizard />
    </div>
  );
}
