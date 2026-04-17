"use client";

import React from "react";
import { cn } from "@/utils/cn";

type BadgeLevel = "pass" | "warn" | "fail" | "neutral" | "info" | "biased" | "marginal" | "fair";

interface BadgeProps {
  level: BadgeLevel;
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}

const levelStyles: Record<BadgeLevel, string> = {
  pass: "bg-success-50 text-success-500",
  warn: "bg-warning-50 text-warning-700",
  fail: "bg-danger-50 text-danger-500",
  neutral: "bg-warm-100 text-warm-500",
  info: "bg-info-50 text-info-700",
  biased: "bg-danger-50 text-danger-500",
  marginal: "bg-warning-50 text-warning-700",
  fair: "bg-success-50 text-success-500",
};

const dotColors: Record<BadgeLevel, string> = {
  pass: "bg-success-500",
  warn: "bg-warning-500",
  fail: "bg-danger-500",
  neutral: "bg-warm-400",
  info: "bg-info-500",
  biased: "bg-danger-500",
  marginal: "bg-warning-500",
  fair: "bg-success-500",
};

export function Badge({ level, children, className, dot = false }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full",
        "text-[11px] font-semibold uppercase tracking-wide",
        levelStyles[level],
        className
      )}
    >
      {dot && (
        <span
          className={cn("w-1.5 h-1.5 rounded-full", dotColors[level])}
        />
      )}
      {children}
    </span>
  );
}
