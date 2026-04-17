"use client";

import React from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";

export default function SettingsPage() {
  return (
    <PageWrapper>
      <PageHeader 
        title="Settings" 
        description="Configure GraphShield AI system preferences and fairness thresholds."
      />

      <div className="max-w-2xl space-y-6">
        <div className="gs-card p-6">
          <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
            Global Fairness Thresholds
          </h3>
          <div className="space-y-4">
            <div>
              <label className="text-[13px] font-semibold text-warm-700 mb-1.5 block">Disparate Impact Threshold</label>
              <input type="number" defaultValue={0.8} step={0.05} className="w-full max-w-[200px] text-[14px] p-2 rounded-lg border border-warm-200 bg-surface focus:ring-2 focus:ring-sage-500/30" />
              <p className="text-[11px] text-warm-400 mt-1">Standard 80% rule applies</p>
            </div>
            <div>
              <label className="text-[13px] font-semibold text-warm-700 mb-1.5 block">Severity Weighting</label>
              <select className="w-full max-w-[200px] text-[14px] p-2 rounded-lg border border-warm-200 bg-surface focus:ring-2 focus:ring-sage-500/30">
                <option>Strict (0 Tolerance)</option>
                <option>Moderate</option>
                <option>Lenient</option>
              </select>
            </div>
          </div>
          <Button className="mt-6">Save Settings</Button>
        </div>
      </div>
    </PageWrapper>
  );
}
