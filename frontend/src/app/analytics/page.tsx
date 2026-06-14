"use client";

import React, { useState, useEffect } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { ChartLine } from "@/components/charts/ChartLine";
import { ChartDonut } from "@/components/charts/ChartDonut";
import { ChartBar } from "@/components/charts/ChartBar";
import { ChartArea } from "@/components/charts/ChartArea";
import { ShieldAlert, ShieldCheck, Shield, Target, Loader2 } from "lucide-react";
import { getAudits, type AuditRun } from "@/lib/systemApi";

export default function AnalyticsPage() {
  const [data, setData] = useState<AuditRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAudits()
      .then((audits) => setData(audits))
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, []);

  // Compute metrics from real audit data
  const totalAudits = data.length;

  let passCount = 0;
  let warnCount = 0;
  let failCount = 0;

  const typeBreakdown: Record<string, number> = {};

  data.forEach((audit) => {
    const s = audit.status?.toLowerCase();
    if (s === "pass") passCount++;
    else if (s === "warn") warnCount++;
    else if (s === "fail") failCount++;

    // Track audit types
    typeBreakdown[audit.type] = (typeBreakdown[audit.type] || 0) + 1;
  });

  const failRate = totalAudits > 0 ? ((failCount / totalAudits) * 100).toFixed(1) : "0";
  const warnRate = totalAudits > 0 ? ((warnCount / totalAudits) * 100).toFixed(1) : "0";
  const passRate = totalAudits > 0 ? ((passCount / totalAudits) * 100).toFixed(1) : "0";

  // Data for charts — score trend over time
  const lineChartData = data
    .filter((d) => d.date && d.score !== undefined)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((d) => ({
      date: new Date(d.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      score: d.score || 0,
    }));

  const donutData = [
    { name: "PASS", value: passCount, color: "#4D6B44" },
    { name: "WARN", value: warnCount, color: "#E8A87C" },
    { name: "FAIL", value: failCount, color: "#C0392B" },
  ].filter((v) => v.value > 0);

  const barChartData = Object.entries(typeBreakdown)
    .map(([name, count]) => ({
      name,
      value: count,
      color: "#4D6B44",
    }))
    .sort((a, b) => b.value - a.value);

  // Audit volume over time (group by date)
  const volumeMap: Record<string, number> = {};
  data.forEach((d) => {
    if (d.date) {
      const key = new Date(d.date).toLocaleDateString(undefined, { month: "short", day: "numeric" });
      volumeMap[key] = (volumeMap[key] || 0) + 1;
    }
  });
  const areaData = Object.entries(volumeMap).map(([date, volume]) => ({ date, volume }));

  if (loading) {
    return (
      <PageWrapper>
        <PageHeader title="Analytics Dashboard" description="Historical bias trends and system-wide fairness intelligence" />
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-sage-500 animate-spin" />
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <PageHeader
        title="Analytics Dashboard"
        description="Historical bias trends and system-wide fairness intelligence"
      />

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard label="Total Audits" value={totalAudits} icon={<Target />} />
        <StatCard label="Failure Rate" value={`${failRate}%`} icon={<ShieldAlert />} trend={failCount > 0 ? "down" : "flat"} />
        <StatCard label="Warning Rate" value={`${warnRate}%`} icon={<Shield />} />
        <StatCard label="Pass Rate" value={`${passRate}%`} icon={<ShieldCheck />} trend={passCount > 0 ? "up" : "flat"} />
      </div>

      {totalAudits === 0 ? (
        <div className="gs-card p-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-warm-100 text-warm-400 flex items-center justify-center mx-auto mb-4">
            <Target className="w-8 h-8" />
          </div>
          <h3 className="font-display text-lg text-warm-800 mb-2">No Analytics Yet</h3>
          <p className="text-sm text-warm-500 max-w-md mx-auto">
            Run your first audit to start seeing trends here. Try the Demo Mode on the Overview page to see what analytics look like with data.
          </p>
        </div>
      ) : (
        <>
          <div className="grid lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2">
              <ChartLine
                data={lineChartData}
                xKey="date"
                lines={[{ key: "score", color: "var(--color-sage-600)", label: "Fairness Score" }]}
                title="Fairness Score Trend"
                height={320}
              />
            </div>
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
            <ChartBar
              data={barChartData}
              title="Audits by Type"
              layout="horizontal"
              height={300}
            />
            <ChartArea
              data={areaData}
              xKey="date"
              areaKey="volume"
              title="Audit Volume Over Time"
              height={300}
            />
          </div>
        </>
      )}
    </PageWrapper>
  );
}
