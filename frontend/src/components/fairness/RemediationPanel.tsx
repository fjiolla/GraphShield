"use client";

import React, { useState } from "react";
import { type RemediationStep } from "@/types/fairness";
import { Badge } from "@/components/ui/Badge";
import { ChevronDown, ChevronUp, CheckCircle2 } from "lucide-react";

interface RemediationPanelProps {
  plan: RemediationStep[];
}

export function RemediationPanel({ plan }: RemediationPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  if (!plan || plan.length === 0) return null;

  return (
    <div className="space-y-4">
      {plan.map((step, idx) => {
        const isExpanded = expandedIndex === idx;
        const p = step.priority.toLowerCase();
        const priorityLevel = (p === "high" || p === "critical") ? "fail" : p === "medium" ? "warn" : "neutral";
        
        return (
          <div key={idx} className="gs-card overflow-hidden">
            <button
              onClick={() => setExpandedIndex(isExpanded ? null : idx)}
              className="w-full px-6 py-5 flex items-start sm:items-center justify-between text-left hover:bg-warm-50 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 pr-4">
                <Badge level={priorityLevel as "fail" | "warn" | "neutral"}>{step.priority}</Badge>
                <h4 className="text-[15px] font-semibold text-warm-800">
                  {step.action}
                </h4>
              </div>
              <div className="text-warm-400 flex-shrink-0 mt-1 sm:mt-0">
                {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </div>
            </button>
            
            {isExpanded && (
              <div className="px-6 pb-6 pt-2 border-t border-warm-100 bg-surface">
                <p className="text-[14px] text-warm-600 leading-relaxed mb-5">
                  {step.description}
                </p>
                <div className="space-y-3">
                  <h5 className="text-[12px] font-bold text-warm-500 uppercase tracking-wider mb-2">
                    Action Steps
                  </h5>
                  {step.steps.map((subStep, j) => (
                    <div key={j} className="flex items-start gap-3">
                      <CheckCircle2 className="w-4 h-4 mt-0.5 text-sage-400 flex-shrink-0" />
                      <span className="text-[14px] text-warm-700">{subStep}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
