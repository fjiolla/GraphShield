"use client";

import React from "react";
import { MetricRow } from "./MetricRow";
import { type UniversalMetrics, type StructuralMetrics } from "@/types/graph";
import { type FairnessScore } from "@/types/fairness";

interface FairnessScorePanelProps {
  title: string;
  universal?: UniversalMetrics;
  structural?: StructuralMetrics;
  flatScores?: FairnessScore[]; // Used by struct-model pipeline
}

function formatName(key: string): string {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function FairnessScorePanel({
  title,
  universal,
  structural,
  flatScores,
}: FairnessScorePanelProps) {
  return (
    <div className="gs-card">
      <div className="px-6 py-4 border-b border-warm-100 bg-warm-50/50 rounded-t-2xl">
        <h3 className="text-[14px] font-semibold text-warm-800 uppercase tracking-wide">
          {title}
        </h3>
      </div>
      
      <div className="px-6 py-2">
        {/* Render struct-model flat scores */}
        {flatScores && flatScores.map((score, i) => (
          <MetricRow
            key={i}
            name={`${score.metric_name} (${score.group})`}
            rawValue={score.raw_value}
            score={score.score}
            status="UNKNOWN"
            flagged={score.flagged}
          />
        ))}

        {/* Render universal metrics */}
        {universal && Object.entries(universal).map(([key, data]) => {
          if (key === "per_group_metrics") return null;
          const metric = data as { raw_value: number; score: number; status: string; per_group?: Record<string, number> };
          return (
            <MetricRow
              key={key}
              name={formatName(key)}
              rawValue={metric.raw_value}
              score={metric.score}
              status={metric.status}
            />
          );
        })}

        {/* Render structural metrics */}
        {structural && Object.entries(structural).map(([key, data]) => {
          const metric = data as { raw_value: number; score: number; status: string; per_group?: Record<string, number> };
          return (
            <MetricRow
              key={key}
              name={formatName(key)}
              rawValue={metric.raw_value}
              score={metric.score}
              status={metric.status}
              perGroup={metric.per_group}
            />
          );
        })}
      </div>
    </div>
  );
}
