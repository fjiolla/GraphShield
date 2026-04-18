"use client";

import React from "react";
import { type GlobalExplanation } from "@/types/graph";
import { TriangleAlert, Info, AlertOctagon } from "lucide-react";
import { cn } from "@/utils/cn";

interface ExplainabilityPanelProps {
  explanation: GlobalExplanation;
}

export function ExplainabilityPanel({ explanation }: ExplainabilityPanelProps) {
  // Guard: backend may return unexpected shape — never crash the page
  if (!explanation) return null;
  const drivers = Array.isArray(explanation.top_bias_drivers) ? explanation.top_bias_drivers : [];
  const summary = explanation.summary ?? "";

  return (
    <div className="gs-card">
      <div className="px-6 py-4 border-b border-warm-100 bg-warm-50/50 rounded-t-2xl">
        <h3 className="text-[14px] font-semibold text-warm-800 uppercase tracking-wide">
          Bias Drivers Analysis
        </h3>
      </div>
      
      <div className="p-6">
        {summary && (
          <p className="text-[14px] text-warm-700 leading-relaxed mb-6 font-medium">
            {summary}
          </p>
        )}

        <div className="space-y-4">
          {drivers.map((driver, i) => {
            let Icon = Info;
            let bgColor = "bg-info-50";
            let textColor = "text-info-700";

            if (driver.severity === "high") {
              Icon = AlertOctagon;
              bgColor = "bg-danger-50";
              textColor = "text-danger-600";
            } else if (driver.severity === "medium") {
              Icon = TriangleAlert;
              bgColor = "bg-warning-50";
              textColor = "text-warning-700";
            }

            return (
              <div 
                key={i} 
                className={cn("p-4 rounded-xl border border-warm-100 flex items-start gap-4 transition-colors hover:bg-warm-50")}
              >
                <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5", bgColor, textColor)}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-[14px] font-bold text-warm-800 mb-1 capitalize">
                    {(driver.factor ?? "").replace(/_/g, " ")} Disparity
                  </h4>
                  <p className="text-[13px] text-warm-600 leading-relaxed">
                    {driver.description ?? ""}
                  </p>
                </div>
              </div>
            );
          })}

          {drivers.length === 0 && (
            <div className="p-6 text-center text-warm-400 bg-warm-50 rounded-xl border border-dashed border-warm-200">
              No significant bias drivers identified.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
