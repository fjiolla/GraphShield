"use client";

import React, { useEffect, useState } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { CheckCircle2, Sparkles, Database, Brain } from "lucide-react";
import api from "@/lib/api";

export default function ConnectionsPage() {
  const [healthStatus, setHealthStatus] = useState<"checking" | "connected" | "offline">("checking");

  useEffect(() => {
    api.get("/health")
      .then(() => setHealthStatus("connected"))
      .catch(() => setHealthStatus("offline"));
  }, []);

  return (
    <PageWrapper>
      <PageHeader 
        title="Connections" 
        description="Manage LLM providers, data sources, and API integrations."
      />

      <div className="grid md:grid-cols-2 gap-6">
        {/* Gemini */}
        <div className="gs-card p-6">
          <div className="flex justify-between items-start mb-4 border-b border-warm-100 pb-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-info-50 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-info-500" />
              </div>
              <h3 className="text-[14px] font-semibold text-warm-800">Google Gemini</h3>
            </div>
            <span className="px-2.5 py-1 bg-success-50 text-success-500 rounded-lg text-[10px] font-bold uppercase flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Connected
            </span>
          </div>
          <p className="text-[13px] text-warm-600 mb-2">Primary LLM provider for AI Chat Assistant, bias explanations, and graph audit reporting.</p>
          <p className="text-[12px] text-warm-400 mb-4">Model: gemini-2.0-flash • Auto-fallback to Groq on rate limit</p>
          <div className="flex items-center gap-2">
            <span className="text-[11px] px-2 py-1 bg-sage-50 text-sage-600 rounded">Google Cloud</span>
            <span className="text-[11px] px-2 py-1 bg-warm-100 text-warm-500 rounded">EU AI Act Compliant</span>
          </div>
        </div>

        {/* Groq */}
        <div className="gs-card p-6">
          <div className="flex justify-between items-start mb-4 border-b border-warm-100 pb-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-sage-50 flex items-center justify-center">
                <Brain className="w-5 h-5 text-sage-500" />
              </div>
              <h3 className="text-[14px] font-semibold text-warm-800">Groq LLM</h3>
            </div>
            <span className="px-2.5 py-1 bg-success-50 text-success-500 rounded-lg text-[10px] font-bold uppercase flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Connected
            </span>
          </div>
          <p className="text-[13px] text-warm-600 mb-2">Fallback provider powering bias profiling, narrative generation, and column classification.</p>
          <p className="text-[12px] text-warm-400 mb-4">Model: llama-3.3-70b-versatile • Ultra-low latency inference</p>
          <div className="flex items-center gap-2">
            <span className="text-[11px] px-2 py-1 bg-sage-50 text-sage-600 rounded">Failover Ready</span>
            <span className="text-[11px] px-2 py-1 bg-warm-100 text-warm-500 rounded">JSON Mode</span>
          </div>
        </div>

        {/* SQLite Knowledge Vault */}
        <div className="gs-card p-6">
          <div className="flex justify-between items-start mb-4 border-b border-warm-100 pb-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-sage-50 flex items-center justify-center">
                <Database className="w-5 h-5 text-sage-500" />
              </div>
              <h3 className="text-[14px] font-semibold text-warm-800">SQLite Knowledge Vault</h3>
            </div>
            <span className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase flex items-center gap-1 ${
              healthStatus === "connected" ? "bg-success-50 text-success-500" : 
              healthStatus === "offline" ? "bg-danger-50 text-danger-500" : "bg-warm-100 text-warm-400"
            }`}>
              <CheckCircle2 className="w-3 h-3" />
              {healthStatus === "connected" ? "Active" : healthStatus === "offline" ? "Offline" : "Checking"}
            </span>
          </div>
          <p className="text-[13px] text-warm-600 mb-2">Local persistent storage for ingested datasets, audit history, and model results.</p>
          <p className="text-[12px] text-warm-400 mb-4">Path: data/local_vault.db • Auto-schema creation</p>
          <div className="flex items-center gap-2">
            <span className="text-[11px] px-2 py-1 bg-sage-50 text-sage-600 rounded">Persistent</span>
            <span className="text-[11px] px-2 py-1 bg-warm-100 text-warm-500 rounded">Zero Config</span>
          </div>
        </div>

        {/* HuggingFace Spaces */}
        <div className="gs-card p-6">
          <div className="flex justify-between items-start mb-4 border-b border-warm-100 pb-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-warning-50 flex items-center justify-center">
                <span className="text-[16px]">🤗</span>
              </div>
              <h3 className="text-[14px] font-semibold text-warm-800">HuggingFace Spaces</h3>
            </div>
            <span className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase flex items-center gap-1 ${
              healthStatus === "connected" ? "bg-success-50 text-success-500" : "bg-warm-100 text-warm-400"
            }`}>
              <CheckCircle2 className="w-3 h-3" />
              {healthStatus === "connected" ? "Deployed" : "Checking"}
            </span>
          </div>
          <p className="text-[13px] text-warm-600 mb-2">Production deployment hosting the FastAPI backend with GPU support for ML inference.</p>
          <p className="text-[12px] text-warm-400 mb-4">URL: fjiolla-graphshield.hf.space • Docker container</p>
          <div className="flex items-center gap-2">
            <span className="text-[11px] px-2 py-1 bg-sage-50 text-sage-600 rounded">Production</span>
            <span className="text-[11px] px-2 py-1 bg-warm-100 text-warm-500 rounded">Auto-scale</span>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
