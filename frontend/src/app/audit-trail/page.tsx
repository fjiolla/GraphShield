"use client";

import React, { useState } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { DataTable } from "@/components/ui/DataTable";
import { Badge } from "@/components/ui/Badge";
import { Search, History } from "lucide-react";
import { formatDateTime } from "@/utils/formatters";

interface AuditRun {
  id: string;
  type: string;
  target: string;
  date: string;
  status: string;
  score: number;
}

// TODO: Connect to explicit backend DB on launch
const MOCK_AUDITS: AuditRun[] = [];

export default function AuditTrailPage() {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredData = MOCK_AUDITS.filter(
    (item) =>
      item.target.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const columns = [
    { key: "id", label: "Run ID", sortable: true, className: "font-mono text-[12px]" },
    { key: "type", label: "Audit Type", sortable: true },
    { key: "target", label: "Target / Asset", sortable: true, className: "font-medium" },
    { key: "date", label: "Date Executed", sortable: true, render: (row: AuditRun) => formatDateTime(row.date) },
    { key: "status", label: "Status", sortable: true, render: (row: AuditRun) => <Badge level={row.status.toLowerCase() as "pass" | "warn" | "fail" | "neutral" | "info"}>{row.status}</Badge> },
    { key: "score", label: "Score", sortable: true, render: (row: AuditRun) => <span className="metric-value font-medium">{row.score}</span> },
  ];

  return (
    <PageWrapper>
      <PageHeader
        title="Audit Trail"
        description="Immutable record of all fairness audits across the organization."
      />

      <div className="gs-card p-6 min-h-[400px]">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-warm-400" />
            <input
              type="text"
              placeholder="Search ID or Asset..."
              className="w-full pl-9 pr-4 py-2 bg-warm-50 border border-warm-200 rounded-xl text-[13px] focus:outline-none focus:ring-2 focus:ring-sage-500/30"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* TODO: Connect to backend GET /api/v1/audits list endpoint once created */}
        {filteredData.length > 0 ? (
          <DataTable
            columns={columns}
            data={filteredData}
            pageSize={10}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-center p-12 mt-8 opacity-75">
            <div className="w-16 h-16 rounded-2xl bg-warm-100 text-warm-400 flex items-center justify-center mb-4">
              <History className="w-8 h-8" />
            </div>
            <h3 className="font-display text-lg text-warm-800 mb-2">No Audits Found</h3>
            <p className="text-sm text-warm-500 max-w-sm">
              {searchTerm
                ? "No previous audits match your search criteria. Try a different query."
                : "Your organization hasn't performed any fairness audits yet."}
            </p>
          </div>
        )}
      </div>
    </PageWrapper>
  );
}
