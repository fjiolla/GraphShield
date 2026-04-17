"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { 
  Activity, 
  ShieldCheck, 
  FileText, 
  Network, 
  Table2, 
  Brain,
  ArrowRight
} from "lucide-react";
import api from "@/lib/api";

interface HealthData {
  status: "up" | "down" | "checking";
  message: string;
}

export default function OverviewDashboard() {
  const [health, setHealth] = useState<HealthData>({ status: "checking", message: "Connecting to API..." });

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.get("/health");
        setHealth({ status: "up", message: "API Connected & Healthy" });
      } catch {
        setHealth({ status: "down", message: "Cannot connect to Backend API" });
      }
    };
    checkHealth();
  }, []);

  return (
    <PageWrapper>
      <PageHeader 
        title="Overview" 
        description="System health and quick audit actions"
      />
      
      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          label="Total Audits" 
          value="24" 
          trend="up" 
          trendValue="12% this week" 
          icon={<Activity />} 
        />
        <StatCard 
          label="Avg Fairness Score" 
          value="82.4" 
          subtext="Across all tracked models" 
          icon={<ShieldCheck />} 
        />
        
        <StatCard 
          label="Knowledge Vault" 
          value="5" 
          subtext="Active SQLite datasets" 
          icon={<Table2 />} 
        />

        {/* API Health Card */}
        <div className="gs-card p-5 relative overflow-hidden group border border-transparent hover:border-warm-200">
          <p className="text-[12px] font-medium text-warm-400 uppercase tracking-wider mb-3">
            System Status
          </p>
          <div className="flex items-center gap-3">
            {health.status === "checking" ? (
              <Badge level="neutral" className="animate-pulse">Checking</Badge>
            ) : health.status === "up" ? (
              <Badge level="pass" dot>Operational</Badge>
            ) : (
              <Badge level="fail" dot>API Offline</Badge>
            )}
          </div>
          <p className="text-[12px] text-warm-500 mt-2">{health.message}</p>
        </div>
      </div>

      {/* Quick Actions Array */}
      <h3 className="font-display text-xl text-warm-800 mb-4 mt-10 border-b border-warm-100 pb-2">
        Start New Audit
      </h3>
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Link href="/audit" className="block group">
          <div className="gs-card p-6 border border-transparent group-hover:border-sage-500 transition-colors">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-sage-50 flex items-center justify-center flex-shrink-0 text-sage-600">
                <FileText className="w-6 h-6" />
              </div>
              <ArrowRight className="w-5 h-5 text-warm-300 group-hover:text-sage-500 transition-colors" />
            </div>
            <h4 className="text-[15px] font-bold text-warm-800 mb-1">Document Profile</h4>
            <p className="text-[13px] text-warm-500 line-clamp-2">
              Analyze free-text PDF or DOCX files for demographic and contextual bias using LLM profiling.
            </p>
          </div>
        </Link>
        
        <Link href="/struct-audit" className="block group">
          <div className="gs-card p-6 border border-transparent group-hover:border-sage-500 transition-colors">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-sage-50 flex items-center justify-center flex-shrink-0 text-sage-600">
                <Table2 className="w-6 h-6" />
              </div>
              <ArrowRight className="w-5 h-5 text-warm-300 group-hover:text-sage-500 transition-colors" />
            </div>
            <h4 className="text-[15px] font-bold text-warm-800 mb-1">Tabular Dataset Audit</h4>
            <p className="text-[13px] text-warm-500 line-clamp-2">
              Calculate predictive parity and disparate impact across CSV or SQLite tables.
            </p>
          </div>
        </Link>

        <Link href="/graph-model-audit" className="block group">
          <div className="gs-card p-6 border border-transparent group-hover:border-sage-500 transition-colors">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-sage-50 flex items-center justify-center flex-shrink-0 text-sage-600">
                <Network className="w-6 h-6" />
              </div>
              <ArrowRight className="w-5 h-5 text-warm-300 group-hover:text-sage-500 transition-colors" />
            </div>
            <h4 className="text-[15px] font-bold text-warm-800 mb-1">Graph Model Pipeline</h4>
            <p className="text-[13px] text-warm-500 line-clamp-2">
              Run full end-to-end structural fairness pipelines on node/edge network structures.
            </p>
          </div>
        </Link>

        <Link href="/model-audit" className="block group">
          <div className="gs-card p-6 border border-transparent group-hover:border-sage-500 transition-colors">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-sage-50 flex items-center justify-center flex-shrink-0 text-sage-600">
                <Brain className="w-6 h-6" />
              </div>
              <ArrowRight className="w-5 h-5 text-warm-300 group-hover:text-sage-500 transition-colors" />
            </div>
            <h4 className="text-[15px] font-bold text-warm-800 mb-1">AI Model Verification</h4>
            <p className="text-[13px] text-warm-500 line-clamp-2">
              Upload trained ML models (.pkl, .pt) alongside ground-truth data for SHAP-based auditing.
            </p>
          </div>
        </Link>
      </div>
    </PageWrapper>
  );
}
