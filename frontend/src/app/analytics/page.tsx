"use client";

import React, { useState, useEffect } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { ChartLine } from "@/components/charts/ChartLine";
import { ChartDonut } from "@/components/charts/ChartDonut";
import { ChartBar } from "@/components/charts/ChartBar";
import { ChartArea } from "@/components/charts/ChartArea";
import { ShieldAlert, ShieldCheck, Shield, Target } from "lucide-react";
import type { GraphModelAuditResult } from "@/types/graph";

// Mock Data representing historical run results matching the schema
const MOCK_HISTORICAL_RUNS: GraphModelAuditResult[] = [];

export default function AnalyticsPage() {
  const [data, setData] = useState<GraphModelAuditResult[]>([]);

  useEffect(() => {
    // TODO: Connect to real GET /api/v1/graph-model-audit/audits endpoint once backend implements it
    // For now, load mock data matching exact schema shape
    setData(MOCK_HISTORICAL_RUNS);
  }, []);

  // Compute metrics from the data array
  const totalAudits = data.length;

  let passCount = 0;
  let warnCount = 0;
  let failCount = 0;
  let scoreSum = 0;

  // Breakdown of failing metrics
  const failReasons: Record<string, number> = {
    "Demographic Parity": 0,
    "Equalized Odds": 0,
    "Disparate Impact": 0,
    "Degree Disparity": 0,
    "Homophily": 0,
    "Clustering Disparity": 0,
  };

  data.forEach((r) => {
    const s = r.scorecard.overall_status;
    if (s === "PASS") passCount++;
    if (s === "WARN") warnCount++;
    if (s === "FAIL") failCount++;
    scoreSum += r.scorecard.overall_score;

    // Check failures
    const u = r.scorecard.universal_metrics;
    const st = r.scorecard.structural_metrics;

    if (u.demographic_parity.status === "FAIL") failReasons["Demographic Parity"]++;
    if (u.equalized_odds.status === "FAIL") failReasons["Equalized Odds"]++;
    if (u.disparate_impact.status === "FAIL") failReasons["Disparate Impact"]++;
    if (st.degree_disparity.status === "FAIL") failReasons["Degree Disparity"]++;
    if (st.homophily_coefficient.status === "FAIL") failReasons["Homophily"]++;
    if (st.clustering_disparity.status === "FAIL") failReasons["Clustering Disparity"]++;
  });

  const avgScore = totalAudits > 0 ? Math.round(scoreSum / totalAudits) : 0;
  const failRate = totalAudits > 0 ? ((failCount / totalAudits) * 100).toFixed(1) : "0";
  const warnRate = totalAudits > 0 ? ((warnCount / totalAudits) * 100).toFixed(1) : "0";

  // Data for charts
  const lineChartData = data.map((d) => ({
    date: new Date(d.scorecard.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    score: d.scorecard.overall_score,
  }));

  const donutData = [
    { name: "PASS", value: passCount, color: "var(--color-success-600)" },
    { name: "WARN", value: warnCount, color: "var(--color-warning-500)" },
    { name: "FAIL", value: failCount, color: "var(--color-danger-600)" },
  ].filter(v => v.value > 0);

  const barChartData = Object.entries(failReasons)
    .filter((entry) => entry[1] > 0)
    .map(([name, count]) => ({
      name,
      value: count,
      color: "var(--color-danger-600)", // Fail color
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <PageWrapper>
      <PageHeader
        title="Analytics Dashboard"
        description="Historical bias trends and system-wide fairness intelligence"
      />

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard label="Total Audited Models" value={totalAudits} icon={<Target />} />
        <StatCard label="Failure Rate" value={`${failRate}%`} icon={<ShieldAlert />} trend="down" trendValue="-2.4%" />
        <StatCard label="Warning Rate" value={`${warnRate}%`} icon={<Shield />} />
        <StatCard label="Average Score" value={avgScore} icon={<ShieldCheck />} />
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        {/* Main trend line */}
        <div className="lg:col-span-2">
          <ChartLine
            data={lineChartData}
            xKey="date"
            lines={[{ key: "score", color: "var(--color-sage-600)", label: "Overall Fairness Score" }]}
            title="Fairness Score Trend"
            height={320}
          />
        </div>

        {/* Status distribution */}
        <div>
          <ChartDonut
            data={donutData}
            title="Audit Status Distribution"
            height={320}
            centerValue={totalAudits.toString()}
            centerLabel="Total"
          />
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Vulnerability breakdown */}
        <ChartBar
          data={barChartData}
          title="Most Frequent Failures (Metric Breaches)"
          layout="horizontal"
          height={300}
        />

        {/* Audit Volume over time */}
        <ChartArea
          data={lineChartData.map(v => ({ ...v, volume: Math.floor(Math.random() * 5) + 1 }))} // Mock volume mapping
          xKey="date"
          areaKey="volume"
          title="Audit Volume Over Time"
          height={300}
        />
      </div>
    </PageWrapper>
  );
}
