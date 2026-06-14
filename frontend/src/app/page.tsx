"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { 
  Activity, 
  ShieldCheck, 
  FileText, 
  Network, 
  Table2, 
  Brain,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import api from "@/lib/api";
import { getAudits } from "@/lib/systemApi";
import { listTables } from "@/lib/structAuditApi";

interface HealthData {
  status: "up" | "down" | "checking";
  message: string;
}

export default function OverviewDashboard() {
  const [health, setHealth] = useState<HealthData>({ status: "checking", message: "Connecting to API..." });
  const [totalAudits, setTotalAudits] = useState<number | null>(null);
  const [avgScore, setAvgScore] = useState<number | null>(null);
  const [tableCount, setTableCount] = useState<number | null>(null);

  useEffect(() => {
    api.get("/health")
      .then(() => setHealth({ status: "up", message: "API Connected & Healthy" }))
      .catch(() => setHealth({ status: "down", message: "Cannot connect to Backend API" }));

    getAudits()
      .then((audits) => {
        setTotalAudits(audits.length);
        if (audits.length > 0) {
          const avg = audits.reduce((sum, a) => sum + (a.score || 0), 0) / audits.length;
          setAvgScore(Math.round(avg));
        } else {
          setAvgScore(0);
        }
      })
      .catch(() => { setTotalAudits(0); setAvgScore(0); });

    listTables()
      .then(({ tables }) => setTableCount(tables.length))
      .catch(() => setTableCount(0));
  }, []);

  return (
    <PageWrapper>
      <PageHeader 
        title="Overview" 
        description="System health and quick audit actions"
      />
      
      {/* Demo Mode Banner */}
      <div className="mb-8">
        <div className="gs-card p-6 border-2 border-dashed border-sage-300 bg-gradient-to-r from-sage-50 to-surface">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-sage-500 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-[15px] font-bold text-warm-800 mb-1">Live Demo Mode</h3>
              <p className="text-[13px] text-warm-500 mb-3">
                Each audit page has a &ldquo;Try Demo&rdquo; button that loads real bias scenarios through the full pipeline — no uploads needed.
              </p>
              <div className="flex flex-wrap gap-2">
                <Link href="/audit">
                  <Button variant="outline" size="sm">Document Demo</Button>
                </Link>
                <Link href="/struct-audit">
                  <Button variant="outline" size="sm">Dataset Demo</Button>
                </Link>
                <Link href="/model-audit">
                  <Button variant="outline" size="sm">Model Demo</Button>
                </Link>
                <Link href="/graph-model-audit">
                  <Button variant="outline" size="sm">Graph Demo</Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          label="Total Audits" 
          value={totalAudits === null ? "—" : totalAudits} 
          subtext={totalAudits === null ? "Loading..." : totalAudits === 0 ? "Awaiting first audit" : `${totalAudits} completed`} 
          icon={<Activity />} 
        />
        <StatCard 
          label="Avg Fairness Score" 
          value={avgScore === null ? "—" : avgScore}
          subtext="Across all tracked models" 
          icon={<ShieldCheck />} 
        />
        
        <StatCard 
          label="Knowledge Vault" 
          value={tableCount === null ? "—" : tableCount} 
          subtext="Active SQLite datasets" 
          icon={<Table2 />} 
        />

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
