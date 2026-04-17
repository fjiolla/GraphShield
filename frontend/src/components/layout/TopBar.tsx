"use client";

import React from "react";
import { usePathname } from "next/navigation";

const ROUTE_TITLES: Record<string, { title: string; description: string }> = {
  "/": {
    title: "Overview",
    description: "System health and recent audit activity",
  },
  "/analytics": {
    title: "Analytics",
    description: "Historical audit insights and trend analysis",
  },
  "/audit": {
    title: "Document Audit",
    description: "NLP-powered bias profiling on text documents",
  },
  "/graph-audit": {
    title: "Graph Audit",
    description: "Structural bias analysis on network graphs",
  },
  "/graph-model-audit": {
    title: "Graph Model Audit",
    description: "Full graph fairness pipeline with scorecard",
  },
  "/model-audit": {
    title: "Model Audit",
    description: "ML model bias detection with SHAP explainability",
  },
  "/struct-audit": {
    title: "Dataset Audit",
    description: "Tabular data fairness analysis and reporting",
  },
  "/audit-trail": {
    title: "Audit Trail",
    description: "Browse saved audit records and scorecards",
  },
  "/connections": {
    title: "Connections",
    description: "Manage integrations and data sources",
  },
  "/settings": {
    title: "Settings",
    description: "Configuration and fairness thresholds",
  },
};

export function TopBar() {
  const pathname = usePathname();
  const route = ROUTE_TITLES[pathname] || {
    title: "GraphShield",
    description: "",
  };

  return (
    <header className="h-16 flex items-center justify-between px-6 bg-surface-alt/80 backdrop-blur-sm sticky top-0 z-30">
      {/* Left — Title */}
      <div>
        <h1 className="text-[15px] font-semibold text-warm-800 leading-tight">
          {route.title}
        </h1>
        {route.description && (
          <p className="text-[12px] text-warm-400 mt-0.5">
            {route.description}
          </p>
        )}
      </div>
    </header>
  );
}
