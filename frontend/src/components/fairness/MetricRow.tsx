"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { formatMetric } from "@/utils/formatters";

interface MetricRowProps {
  name: string;
  rawValue: number | null;
  score: number | null;
  status: "PASS" | "WARN" | "FAIL" | "UNKNOWN" | string;
  flagged?: boolean; // For struct-model-audit schema
  perGroup?: Record<string, number>;
}

export function MetricRow({
  name,
  rawValue,
  score,
  status,
  flagged,
  perGroup,
}: MetricRowProps) {
  // Determine if it failed based on status OR flagged
  const isFailed = status === "FAIL" || flagged;
  const isWarn = status === "WARN";
  const finalStatus = isFailed ? "fail" : isWarn ? "warn" : "pass";

  return (
    <div className="py-4 border-b border-warm-100 last:border-0 flex flex-col sm:flex-row sm:items-center gap-4">
      {/* Metric Name & Badge */}
      <div className="w-full sm:w-1/3 flex items-start sm:items-center justify-between sm:justify-start gap-4">
        <span className="text-[13px] font-medium text-warm-800">{name}</span>
        <Badge level={finalStatus as "pass" | "warn" | "fail" | "neutral" | "info"} dot>
          {status !== "UNKNOWN" ? status : flagged ? "FLAGGED" : "OK"}
        </Badge>
      </div>

      {/* Raw Value */}
      <div className="w-full sm:w-1/5 text-left sm:text-right">
        <span className="text-[12px] text-warm-500 uppercase tracking-wide block sm:hidden mb-1">
          Raw Value
        </span>
        <span className="text-[14px] font-medium text-warm-800 metric-value">
          {rawValue !== null ? formatMetric(rawValue, 4) : "—"}
        </span>
      </div>

      {/* Score Bar */}
      <div className="w-full sm:w-1/3 ml-auto">
        {score !== null ? (
          <ProgressBar value={score} showLabel />
        ) : (
          <span className="text-[13px] text-warm-400">N/A</span>
        )}
      </div>

      {/* Per-group details (Optional accordion in future, for now just show if minimal) */}
      {perGroup && Object.keys(perGroup).length > 0 && (
        <div className="w-full mt-2 sm:mt-0 text-[11px] text-warm-400">
          <div className="flex flex-wrap gap-2">
            {Object.entries(perGroup).map(([group, val], i) => (
              <span key={i} className="bg-warm-100 px-2 py-0.5 rounded text-warm-600">
                {group}: <span className="metric-value font-medium">{formatMetric(val, 2)}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
