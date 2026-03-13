"use client";

import { useState } from "react";
import { useWizardStore, type WizardContext } from "@/lib/store/wizardStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface StepContextProps {
  onNext: () => void;
  onBack: () => void;
}

const AUDIENCE_TYPES = ["Broad", "Lookalike", "Retargeting", "Interest", "Custom"];

export function StepContext({ onNext, onBack }: StepContextProps) {
  const { context, setContext } = useWizardStore();
  const [form, setForm] = useState<WizardContext>({
    ...context,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!form.product.trim()) newErrors.product = "Product name is required";
    if (!form.audience_type) newErrors.audience_type = "Audience type is required";
    if (!form.daily_budget || form.daily_budget < 100) {
      newErrors.daily_budget = "Daily budget must be at least $1 (100 cents)";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleContinue = () => {
    if (!validate()) return;
    setContext(form);
    onNext();
  };

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="product">
          Product / Brand Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="product"
          placeholder="e.g. AirMax, SummerCollection"
          value={form.product}
          onChange={(e) => setForm({ ...form, product: e.target.value })}
          className={errors.product ? "border-destructive" : ""}
        />
        {errors.product && (
          <p className="text-sm text-destructive">{errors.product}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="audience-type">
          Audience Type <span className="text-destructive">*</span>
        </Label>
        <Select
          value={form.audience_type}
          onValueChange={(val) => setForm({ ...form, audience_type: val })}
        >
          <SelectTrigger id="audience-type" className={errors.audience_type ? "border-destructive" : ""}>
            <SelectValue placeholder="Select audience type" />
          </SelectTrigger>
          <SelectContent>
            {AUDIENCE_TYPES.map((type) => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.audience_type && (
          <p className="text-sm text-destructive">{errors.audience_type}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="daily-budget">
          Daily Budget (cents) <span className="text-destructive">*</span>
        </Label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
            ¢
          </span>
          <Input
            id="daily-budget"
            type="number"
            min={100}
            step={100}
            placeholder="1000"
            value={form.daily_budget}
            onChange={(e) =>
              setForm({ ...form, daily_budget: parseInt(e.target.value) || 0 })
            }
            className={`pl-7 ${errors.daily_budget ? "border-destructive" : ""}`}
          />
        </div>
        <p className="text-xs text-muted-foreground">
          {form.daily_budget >= 100
            ? `= $${(form.daily_budget / 100).toFixed(2)} / day`
            : "Minimum $1.00 / day"}
        </p>
        {errors.daily_budget && (
          <p className="text-sm text-destructive">{errors.daily_budget}</p>
        )}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button onClick={handleContinue} className="flex-1">
          Continue
        </Button>
      </div>
    </div>
  );
}
