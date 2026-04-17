"use client";

import React from "react";
import { type NarrativeSection as NarrativeType } from "@/types/fairness";
import { Sparkles } from "lucide-react";

interface NarrativeSectionProps {
  narrative: NarrativeType[];
}

export function NarrativeSection({ narrative }: NarrativeSectionProps) {
  if (!narrative || narrative.length === 0) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-6">
        <Sparkles className="w-5 h-5 text-sage-500" />
        <h3 className="text-lg font-bold text-warm-800">AI Intelligence Report</h3>
      </div>
      
      {narrative.map((section, i) => (
        <div key={i} className="gs-card p-6">
          <h4 className="text-[15px] font-bold text-warm-800 mb-3 border-b border-warm-100 pb-2">
            {section.title}
          </h4>
          <div className="prose prose-sm prose-warm max-w-none text-warm-700 leading-relaxed space-y-4">
            {section.content.split("\n\n").map((paragraph, j) => (
              <p key={j}>{paragraph}</p>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
