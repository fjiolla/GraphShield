"use client";

import React from "react";
import { cn } from "@/utils/cn";

interface ProgressBarProps {
  value: number; // 0–100
  max?: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

function getBarColor(value: number): string {
  if (value >= 80) return "bg-success-500";
  if (value >= 60) return "bg-warning-500";
  return "bg-danger-500";
}

export function ProgressBar({
  value,
  max = 100,
  size = "md",
  showLabel = false,
  className,
}: ProgressBarProps) {
  const percent = Math.min(Math.max((value / max) * 100, 0), 100);

  const heights: Record<string, string> = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-4",
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          "flex-1 rounded-full bg-warm-100 overflow-hidden",
          heights[size]
        )}
      >
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500 ease-out",
            getBarColor(value)
          )}
          style={{ width: `${percent}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-[12px] font-medium text-warm-500 metric-value w-10 text-right">
          {Math.round(value)}
        </span>
      )}
    </div>
  );
}
