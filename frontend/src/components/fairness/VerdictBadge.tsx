"use client";

import React from "react";
import { cn } from "@/utils/cn";
import { verdictColor } from "@/utils/fairnessHelpers";
import { ShieldAlert, ShieldCheck, Shield } from "lucide-react";

interface VerdictBadgeProps {
  verdict: "BIASED" | "MARGINAL" | "FAIR" | string;
  confidence?: string;
  className?: string;
}

export function VerdictBadge({ verdict, confidence, className }: VerdictBadgeProps) {
  const v = verdict as "BIASED" | "MARGINAL" | "FAIR";
  const colors = verdictColor(v);
  
  let Icon = ShieldAlert;
  if (v === "FAIR") Icon = ShieldCheck;
  if (v === "MARGINAL") Icon = Shield;

  return (
    <div
      className={cn(
        "inline-flex flex-col items-center justify-center p-6 rounded-2xl border-2",
        colors.bg,
        colors.border,
        className
      )}
    >
      <Icon className={cn("w-12 h-12 mb-3", colors.text)} />
      <span className={cn("text-2xl font-bold tracking-tight", colors.text)}>
        {verdict}
      </span>
      {confidence && (
        <span className={cn("text-[13px] font-medium mt-1 opacity-80", colors.text)}>
          {confidence} Confidence
        </span>
      )}
    </div>
  );
}
