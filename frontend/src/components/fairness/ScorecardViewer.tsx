"use client";

import React from "react";
import { type Scorecard } from "@/types/graph";
import { FairnessScorePanel } from "./FairnessScorePanel";
import { Badge } from "@/components/ui/Badge";
import { scoreColor } from "@/utils/fairnessHelpers";

interface ScorecardViewerProps {
  scorecard: Scorecard;
}

export function ScorecardViewer({ scorecard }: ScorecardViewerProps) {
  return (
    <div className="space-y-6">
      {/* Overview Head */}
      <div className="gs-card p-8 flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-3 mb-1">
            <h2 className="font-display text-xl font-bold text-warm-800">Fairness Scorecard</h2>
            <Badge level={scorecard.overall_status.toLowerCase() as "pass" | "warn" | "fail" | "neutral" | "info"}>
              {scorecard.overall_status}
            </Badge>
          </div>
          <p className="text-[13px] text-warm-500 max-w-xl leading-relaxed">
            Protected attribute: <span className="font-semibold text-warm-700">{scorecard.protected_attribute}</span>{" "}
            across groups ({scorecard.groups_found.join(", ")}).
          </p>
        </div>

        <div className="flex-shrink-0 text-center">
          <div className="relative inline-flex items-center justify-center">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="40"
                strokeWidth="8"
                stroke="#E8E6E0"
                fill="none"
              />
              <circle
                cx="48"
                cy="48"
                r="40"
                strokeWidth="8"
                stroke="currentColor"
                fill="none"
                strokeDasharray="251.2"
                strokeDashoffset={251.2 - (251.2 * scorecard.overall_score) / 100}
                className={scoreColor(scorecard.overall_score)}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-2xl font-bold metric-value ${scoreColor(scorecard.overall_score)}`}>
                {scorecard.overall_score}
              </span>
            </div>
          </div>
          <p className="text-[11px] font-medium text-warm-400 mt-2 uppercase tracking-wide">
            Overall Score
          </p>
        </div>
      </div>

      {/* Metrics Panels */}
      <div className="grid lg:grid-cols-2 gap-6">
        <FairnessScorePanel 
          title="Universal Fairness" 
          universal={scorecard.universal_metrics} 
        />
        <FairnessScorePanel 
          title="Structural Fairness" 
          structural={scorecard.structural_metrics} 
        />
      </div>
    </div>
  );
}
