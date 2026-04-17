"use client";

import React from "react";
import { cn } from "@/utils/cn";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: "up" | "down" | "flat";
  trendValue?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({
  label,
  value,
  subtext,
  trend,
  trendValue,
  icon,
  className,
}: StatCardProps) {
  return (
    <div className={cn("gs-card p-5", className)}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-[12px] font-medium text-warm-400 uppercase tracking-wider">
          {label}
        </p>
        {icon && (
          <div className="w-9 h-9 rounded-xl bg-sage-50 flex items-center justify-center text-sage-500">
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-end gap-3">
        <p className="text-2xl font-semibold text-warm-800 tracking-tight metric-value">
          {value}
        </p>
        {trend && (
          <div
            className={cn(
              "flex items-center gap-0.5 text-[12px] font-medium pb-0.5",
              trend === "up" && "text-success-500",
              trend === "down" && "text-danger-500",
              trend === "flat" && "text-warm-400"
            )}
          >
            {trend === "up" && <TrendingUp className="w-3.5 h-3.5" />}
            {trend === "down" && <TrendingDown className="w-3.5 h-3.5" />}
            {trend === "flat" && <Minus className="w-3.5 h-3.5" />}
            {trendValue && <span>{trendValue}</span>}
          </div>
        )}
      </div>

      {subtext && (
        <p className="text-[12px] text-warm-400 mt-1.5">{subtext}</p>
      )}
    </div>
  );
}
