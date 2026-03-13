"use client";

import { useState } from "react";
import { useWizardStore } from "@/lib/store/wizardStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle, FolderOpen } from "lucide-react";

interface StepDriveUrlProps {
  onNext: () => void;
  onBack: () => void;
}

const DRIVE_URL_PATTERN =
  /^https:\/\/drive\.google\.com\/(drive\/folders\/|file\/d\/|open\?id=)[a-zA-Z0-9_-]+/;

export function StepDriveUrl({ onNext, onBack }: StepDriveUrlProps) {
  const { driveUrl, setDriveUrl } = useWizardStore();
  const [inputValue, setInputValue] = useState(driveUrl);
  const [touched, setTouched] = useState(false);

  const isValid = DRIVE_URL_PATTERN.test(inputValue.trim());
  const showError = touched && inputValue.trim().length > 0 && !isValid;

  const handleContinue = () => {
    setTouched(true);
    if (!isValid) return;
    setDriveUrl(inputValue.trim());
    onNext();
  };

  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-muted/40 p-4 text-sm text-muted-foreground">
        <div className="flex gap-2">
          <FolderOpen className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <div>
            <p className="font-medium text-foreground">Accepted formats</p>
            <ul className="mt-1 space-y-0.5 text-xs">
              <li>Folder: <code>https://drive.google.com/drive/folders/ABC123</code></li>
              <li>File: <code>https://drive.google.com/file/d/ABC123/view</code></li>
            </ul>
            <p className="mt-2 text-xs">
              Make sure the folder is shared with the service account.
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="drive-url">Google Drive URL</Label>
        <Input
          id="drive-url"
          placeholder="https://drive.google.com/drive/folders/..."
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setTouched(false);
          }}
          onBlur={() => setTouched(true)}
          className={showError ? "border-destructive focus-visible:ring-destructive" : ""}
        />
        {showError && (
          <p className="flex items-center gap-1 text-sm text-destructive">
            <AlertCircle className="h-3.5 w-3.5" />
            Please enter a valid Google Drive URL
          </p>
        )}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button
          onClick={handleContinue}
          disabled={!inputValue.trim()}
          className="flex-1"
        >
          Continue
        </Button>
      </div>
    </div>
  );
}
