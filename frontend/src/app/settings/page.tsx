"use client";

import React, { useState, useEffect } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { CheckCircle2 } from "lucide-react";
import toast from "react-hot-toast";

interface AppSettings {
  disparateImpactThreshold: number;
  severityWeighting: string;
  autoRunRemediation: boolean;
  exportFormat: string;
  darkMode: boolean;
}

const DEFAULT_SETTINGS: AppSettings = {
  disparateImpactThreshold: 0.8,
  severityWeighting: "Moderate",
  autoRunRemediation: false,
  exportFormat: "pdf",
  darkMode: false,
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("graphshield_settings");
    if (stored) {
      try {
        setSettings(JSON.parse(stored));
      } catch {
        // ignore
      }
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem("graphshield_settings", JSON.stringify(settings));
    setSaved(true);
    toast.success("Settings saved successfully");
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <PageWrapper>
      <PageHeader 
        title="Settings" 
        description="Configure GraphShield AI system preferences and fairness thresholds."
      />

      <div className="max-w-2xl space-y-6">
        {/* Fairness Thresholds */}
        <div className="gs-card p-6">
          <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
            Global Fairness Thresholds
          </h3>
          <div className="space-y-5">
            <div>
              <label className="text-[13px] font-semibold text-warm-700 mb-1.5 block">Disparate Impact Threshold</label>
              <input
                type="number"
                value={settings.disparateImpactThreshold}
                onChange={(e) => setSettings({ ...settings, disparateImpactThreshold: parseFloat(e.target.value) || 0.8 })}
                step={0.05}
                min={0.5}
                max={1.0}
                className="w-full max-w-[200px] text-[14px] p-2.5 rounded-lg border border-warm-200 bg-surface focus:ring-2 focus:ring-sage-500/30 focus:outline-none"
              />
              <p className="text-[11px] text-warm-400 mt-1">Standard 80% rule (4/5ths rule) per EEOC guidelines</p>
            </div>
            <div>
              <label className="text-[13px] font-semibold text-warm-700 mb-1.5 block">Severity Weighting</label>
              <select
                value={settings.severityWeighting}
                onChange={(e) => setSettings({ ...settings, severityWeighting: e.target.value })}
                className="w-full max-w-[200px] text-[14px] p-2.5 rounded-lg border border-warm-200 bg-surface focus:ring-2 focus:ring-sage-500/30 focus:outline-none"
              >
                <option value="Strict (0 Tolerance)">Strict (0 Tolerance)</option>
                <option value="Moderate">Moderate</option>
                <option value="Lenient">Lenient</option>
              </select>
              <p className="text-[11px] text-warm-400 mt-1">How aggressively to flag borderline metrics</p>
            </div>
          </div>
        </div>

        {/* Export Settings */}
        <div className="gs-card p-6">
          <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
            Report & Export
          </h3>
          <div className="space-y-5">
            <div>
              <label className="text-[13px] font-semibold text-warm-700 mb-1.5 block">Default Export Format</label>
              <select
                value={settings.exportFormat}
                onChange={(e) => setSettings({ ...settings, exportFormat: e.target.value })}
                className="w-full max-w-[200px] text-[14px] p-2.5 rounded-lg border border-warm-200 bg-surface focus:ring-2 focus:ring-sage-500/30 focus:outline-none"
              >
                <option value="pdf">PDF Report</option>
                <option value="json">JSON (Machine-readable)</option>
                <option value="csv">CSV Summary</option>
              </select>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="autoRemediation"
                checked={settings.autoRunRemediation}
                onChange={(e) => setSettings({ ...settings, autoRunRemediation: e.target.checked })}
                className="w-4 h-4 rounded border-warm-300 text-sage-500 focus:ring-sage-500"
              />
              <label htmlFor="autoRemediation" className="text-[13px] text-warm-700">
                Auto-generate remediation plan after each audit
              </label>
            </div>
          </div>
        </div>

        {/* LLM Provider Settings */}
        <div className="gs-card p-6">
          <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
            AI Provider Configuration
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between bg-warm-50 rounded-xl px-4 py-3">
              <div>
                <p className="text-[13px] font-medium text-warm-700">Primary: Google Gemini</p>
                <p className="text-[11px] text-warm-400">gemini-2.0-flash</p>
              </div>
              <span className="text-[11px] px-2 py-1 bg-success-50 text-success-500 rounded-lg font-medium">Active</span>
            </div>
            <div className="flex items-center justify-between bg-warm-50 rounded-xl px-4 py-3">
              <div>
                <p className="text-[13px] font-medium text-warm-700">Fallback: Groq (Llama 3.3 70B)</p>
                <p className="text-[11px] text-warm-400">Auto-activates on Gemini rate limit</p>
              </div>
              <span className="text-[11px] px-2 py-1 bg-warm-100 text-warm-500 rounded-lg font-medium">Standby</span>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <Button onClick={handleSave} size="lg" className="gap-2">
          {saved ? <CheckCircle2 className="w-4 h-4" /> : null}
          {saved ? "Saved!" : "Save Settings"}
        </Button>
      </div>
    </PageWrapper>
  );
}
