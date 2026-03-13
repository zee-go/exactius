"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { WIZARD_STEPS } from "@/lib/store/wizardStore";

interface WizardProgressProps {
  currentStep: number;
}

export function WizardProgress({ currentStep }: WizardProgressProps) {
  return (
    <nav className="flex items-center gap-0">
      {WIZARD_STEPS.map((step, index) => {
        const isCompleted = step.id < currentStep;
        const isCurrent = step.id === currentStep;

        return (
          <div key={step.id} className="flex items-center">
            <div className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors",
                  isCompleted && "bg-primary text-primary-foreground",
                  isCurrent && "border-2 border-primary bg-background text-primary",
                  !isCompleted && !isCurrent && "border-2 border-muted bg-background text-muted-foreground"
                )}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : step.id}
              </div>
              <span
                className={cn(
                  "text-xs",
                  isCurrent ? "font-medium text-primary" : "text-muted-foreground"
                )}
              >
                {step.label}
              </span>
            </div>

            {index < WIZARD_STEPS.length - 1 && (
              <div
                className={cn(
                  "mx-2 mt-[-14px] h-0.5 w-12 flex-1 transition-colors",
                  step.id < currentStep ? "bg-primary" : "bg-muted"
                )}
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}
