"use client";

import React, { useState, useEffect } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { DropZone } from "@/components/ui/DropZone";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useStructStore } from "@/stores/useStructStore";
import { AlertCircle, Table2, Check, ArrowRight, Clock } from "lucide-react";
import { StatCard } from "@/components/ui/StatCard";

export default function StructAuditPage() {
  const { 
    uploadFile, setUploadFile, upload, uploadResult, isUploading,
    startAudit, isAuditing, runAuditResult,
    report, isFetchingReport, fetchReport,
    reset, error 
  } = useStructStore();

  const [waitTimer, setWaitTimer] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isAuditing) {
      setWaitTimer(0);
      interval = setInterval(() => {
        setWaitTimer((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isAuditing]);

  // FIX: Trigger fetchReport once runAuditResult is successfully populated
  useEffect(() => {
    if (runAuditResult && !report && !isFetchingReport) {
      fetchReport();
    }
  }, [runAuditResult, report, isFetchingReport, fetchReport]);

  const handleUpload = () => upload();
  const handleRunAudit = () => startAudit();

  return (
    <PageWrapper>
      <PageHeader 
        title="Dataset Fairness Audit" 
        description="Ingest tabular datasets (CSV, Excel) to an isolated SQLite vault and run LLM-powered universal fairness evaluation."
        actions={
          (uploadResult || report) ? (
            <Button variant="outline" size="sm" onClick={reset}>
              Start New Flow
            </Button>
          ) : undefined
        }
      />

      <div className="grid lg:grid-cols-12 gap-8">
        <div className="lg:col-span-4 space-y-6">
          <div className="gs-card p-6 border-l-4 border-l-sage-500">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[13px] font-bold ${uploadResult ? 'bg-success-500 text-white' : 'bg-sage-500 text-white shadow-card'}`}>
                 {uploadResult ? <Check className="w-4 h-4"/> : "1"}
              </div>
              <h3 className="font-display text-[16px] font-semibold text-warm-800">1. Ingest Data</h3>
            </div>
            
            {!uploadResult ? (
              <div className="space-y-4">
                <DropZone
                  onFileSelect={setUploadFile}
                  selectedFile={uploadFile}
                  onClear={() => setUploadFile(null)}
                  disabled={isUploading}
                  className="p-4"
                  accept={{ "text/csv": [".csv"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"] }}
                />
                <Button className="w-full" onClick={handleUpload} disabled={!uploadFile || isUploading} loading={isUploading}>
                  Upload & Ingest to Vault
                </Button>
              </div>
            ) : (
               <div className="p-4 bg-success-50 text-success-700 rounded-xl text-[13px] flex items-center gap-2">
                 <Check className="w-5 h-5 flex-shrink-0" />
                 Dataset successfully ingested to SQLite vault.
               </div>
            )}
          </div>

          <div className={`gs-card p-6 border-l-4 ${uploadResult && !runAuditResult ? 'border-l-sage-500' : 'border-l-warm-200'} ${uploadResult ? 'opacity-100' : 'opacity-50'}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[13px] font-bold ${runAuditResult ? 'bg-success-500 text-white' : uploadResult && !runAuditResult ? 'bg-sage-500 text-white shadow-card' : 'bg-warm-200 text-warm-500'}`}>
                 {runAuditResult ? <Check className="w-4 h-4"/> : "2"}
              </div>
              <h3 className="font-display text-[16px] font-semibold text-warm-800">2. Run Groq Audit</h3>
            </div>

            {uploadResult && !runAuditResult && !isAuditing && (
              <Button className="w-full flex justify-between" onClick={handleRunAudit}>
                Start AI Analysis <ArrowRight className="w-4 h-4"/>
              </Button>
            )}

            {isAuditing && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-warm-700 font-medium">
                  <div className="flex items-center gap-2">
                     <Clock className="w-4 h-4 text-warning-500 animate-pulse"/>
                     <span>Processing...</span>
                  </div>
                  <span className="metric-value">{waitTimer}s</span>
                </div>
                <div className="w-full bg-warm-100 rounded-full h-2">
                  <div className="bg-sage-500 h-2 rounded-full transition-all duration-1000 ease-linear" style={{ width: `${Math.min((waitTimer/65)*100, 100)}%` }} />
                </div>
                <p className="text-[12px] text-warm-500 leading-relaxed text-center">
                  Processing via Groq AI — this takes ~60 seconds due to rate limits on complex dataset profiling.
                </p>
              </div>
            )}

             {runAuditResult && (
               <div className="p-4 bg-success-50 text-success-700 rounded-xl text-[13px] flex items-center gap-2">
                 <Check className="w-5 h-5 flex-shrink-0" />
                 Analysis complete.
               </div>
            )}
          </div>

          <div className={`gs-card p-6 border-l-4 ${runAuditResult ? 'border-l-sage-500' : 'border-l-warm-200'} ${runAuditResult ? 'opacity-100' : 'opacity-50'}`}>
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[13px] font-bold ${report ? 'bg-success-500 text-white' : runAuditResult ? 'bg-sage-500 text-white shadow-card' : 'bg-warm-200 text-warm-500'}`}>
                 3
              </div>
              <h3 className="font-display text-[16px] font-semibold text-warm-800">3. View Report</h3>
            </div>
            {isFetchingReport && <div className="mt-4 text-warm-500 text-sm animate-pulse">Fetching intelligence report...</div>}
            {report && <div className="mt-4 text-success-600 font-medium text-sm">Report ready</div>}
          </div>

          {error && (
            <div className="p-3 bg-danger-50 text-danger-600 rounded-xl text-[13px] flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>{error}</p>
            </div>
          )}
        </div>

        <div className="lg:col-span-8">
          {!uploadResult && !isUploading && (
             <div className="h-full min-h-[400px] border-2 border-dashed border-warm-200 rounded-2xl flex flex-col items-center justify-center text-center p-8">
               <div className="w-16 h-16 rounded-2xl bg-warm-100 text-warm-400 flex items-center justify-center mb-4">
                 <Table2 className="w-8 h-8" />
               </div>
               <h3 className="font-display text-lg text-warm-800 mb-2">Awaiting Dataset</h3>
               <p className="text-sm text-warm-500 max-w-sm">
                 Upload a CSV or Excel file on the left to begin the ingestion process into the secure SQLite vault.
               </p>
             </div>
          )}

          {isUploading && (
            <div className="h-full min-h-[400px] gs-card p-8 flex flex-col items-center justify-center text-center space-y-6">
              <div className="relative w-20 h-20">
                 <div className="absolute inset-0 border-4 border-sage-100 rounded-full"></div>
                 <div className="absolute inset-0 border-4 border-sage-500 rounded-full border-t-transparent animate-spin"></div>
              </div>
              <div>
                <h3 className="font-display text-lg text-warm-800 mb-1">Ingesting Data...</h3>
                <p className="text-sm text-warm-500">Creating vault schema and storing tabular records.</p>
              </div>
            </div>
          )}

          {uploadResult && !report && !isFetchingReport && (
            <div className="gs-card p-8 animate-fade-in space-y-6">
              <h2 className="font-display text-xl text-warm-800 mb-2">Ingestion Successful</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                 <StatCard label="Table Name" value={uploadResult.ingestion.table_name} />
                 <StatCard label="Row Count" value={uploadResult.ingestion.row_count} />
                 <StatCard label="Column Count" value={uploadResult.ingestion.column_count} />
              </div>
              <div className="mt-4 p-4 bg-warm-50 rounded-xl text-warm-700 text-sm">
                 <strong>Detected Columns:</strong> {Array.isArray(uploadResult.ingestion.columns) ? uploadResult.ingestion.columns.join(", ") : String(uploadResult.ingestion.columns)}
              </div>
            </div>
          )}

          {report && (
            <div className="space-y-6 animate-fade-in">
              <div className="gs-card p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div>
                  <h2 className="font-display text-xl text-warm-800 mb-2">Fairness Report Generated</h2>
                  <p className="text-warm-500 text-[14px]">Dataset evaluated against universal fairness criteria.</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-3 items-center">
                  <div className="flex-shrink-0 bg-warm-50 px-6 py-4 rounded-xl border border-warm-100 text-center">
                    <p className="text-[11px] font-bold text-warm-500 uppercase tracking-widest mb-2">Overall Risk</p>
                    <Badge 
                      level={report.risk_level === "High" ? "fail" : report.risk_level === "Medium" ? "warn" : "pass"} 
                      className="px-4 py-1.5 text-sm"
                    >
                      {report.risk_level || "UNKNOWN"}
                    </Badge>
                  </div>
                  <button
                    onClick={() => {
                      const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `graphshield_report_${new Date().toISOString().slice(0,10)}.json`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="px-4 py-2 rounded-xl border border-warm-200 bg-white text-warm-700 text-[13px] font-medium hover:bg-warm-50 transition-colors flex items-center gap-2"
                  >
                    ↓ Download Report
                  </button>
                </div>
              </div>

              {/* Summary */}
              {report.summary && (
                <div className="gs-card p-6">
                  <h3 className="text-[14px] font-semibold text-warm-800 mb-3 uppercase tracking-wide border-b border-warm-100 pb-2">Summary</h3>
                  <p className="text-[14px] text-warm-700 leading-relaxed">{report.summary}</p>
                </div>
              )}

              {/* Dataset Overview */}
              {report.dataset_overview ? (
                <div className="gs-card p-6">
                  <h3 className="text-[14px] font-semibold text-warm-800 mb-4 uppercase tracking-wide border-b border-warm-100 pb-2">Dataset Overview</h3>
                  <div className="grid sm:grid-cols-3 gap-4">
                    {report.dataset_overview.table_name && (
                      <div className="bg-warm-50 rounded-xl p-4">
                        <p className="text-[11px] font-semibold text-warm-400 uppercase tracking-wider mb-1">Table Name</p>
                        <p className="text-[18px] font-bold text-warm-800 metric-value">{report.dataset_overview.table_name}</p>
                      </div>
                    )}
                    {report.dataset_overview.total_rows !== undefined && (
                      <div className="bg-warm-50 rounded-xl p-4">
                        <p className="text-[11px] font-semibold text-warm-400 uppercase tracking-wider mb-1">Total Rows</p>
                        <p className="text-[18px] font-bold text-warm-800 metric-value">{report.dataset_overview.total_rows}</p>
                      </div>
                    )}
                    {report.dataset_overview.total_columns !== undefined && (
                      <div className="bg-warm-50 rounded-xl p-4">
                        <p className="text-[11px] font-semibold text-warm-400 uppercase tracking-wider mb-1">Total Columns</p>
                        <p className="text-[18px] font-bold text-warm-800 metric-value">{report.dataset_overview.total_columns}</p>
                      </div>
                    )}
                  </div>
                  {Array.isArray(report.dataset_overview.sensitive_columns) && report.dataset_overview.sensitive_columns.length > 0 && (
                    <div className="mt-4">
                      <p className="text-[12px] font-semibold text-warm-500 uppercase tracking-wider mb-2">Sensitive Columns</p>
                      <div className="flex flex-wrap gap-2">
                        {report.dataset_overview.sensitive_columns.map((c: string, i: number) => (
                          <span key={i} className="px-3 py-1 bg-danger-50 text-danger-700 rounded-lg text-[12px] font-medium border border-danger-100">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {Array.isArray(report.dataset_overview.target_columns) && report.dataset_overview.target_columns.length > 0 && (
                    <div className="mt-4">
                      <p className="text-[12px] font-semibold text-warm-500 uppercase tracking-wider mb-2">Target Columns</p>
                      <div className="flex flex-wrap gap-2">
                        {report.dataset_overview.target_columns.map((c: string, i: number) => (
                          <span key={i} className="px-3 py-1 bg-info-50 text-info-700 rounded-lg text-[12px] font-medium border border-info-100">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {Array.isArray(report.dataset_overview.proxy_columns) && report.dataset_overview.proxy_columns.length > 0 && (
                    <div className="mt-4">
                      <p className="text-[12px] font-semibold text-warm-500 uppercase tracking-wider mb-2">Proxy Columns</p>
                      <div className="flex flex-wrap gap-2">
                        {report.dataset_overview.proxy_columns.map((c: string, i: number) => (
                          <span key={i} className="px-3 py-1 bg-warning-50 text-warning-700 rounded-lg text-[12px] font-medium border border-warning-100">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : null}

              {/* Bias Metrics (Legacy Schema Support) */}
              {report.bias_metrics && typeof report.bias_metrics === 'object' && Object.keys(report.bias_metrics).length > 0 && (
                <div className="gs-card p-6">
                  <h3 className="text-[14px] font-semibold text-warm-800 mb-4 uppercase tracking-wide border-b border-warm-100 pb-2">Bias Metrics</h3>
                  <div className="grid sm:grid-cols-2 gap-4">
                    {Object.entries(report.bias_metrics).map(([k, v]) => (
                      <div key={k} className="flex justify-between items-center p-3 bg-warm-50 rounded-xl border border-warm-100">
                        <span className="text-[13px] text-warm-600 font-medium">{k.replace(/_/g," ")}</span>
                        <span className="text-[13px] font-bold text-warm-800 metric-value">
                          {typeof v === "number" ? v.toFixed(4) : typeof v === "object" ? JSON.stringify(v) : String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metrics Summary (New Schema Support) */}
              {report.metrics_summary && typeof report.metrics_summary === 'object' && Object.keys(report.metrics_summary).length > 0 && (
                <div className="gs-card p-6">
                  <h3 className="text-[14px] font-semibold text-warm-800 mb-4 uppercase tracking-wide border-b border-warm-100 pb-2">Disparate Impact & Parity</h3>
                  <div className="grid sm:grid-cols-2 gap-4">
                    {Object.entries(report.metrics_summary).map(([colPair, rawMetrics]) => {
                      const metrics = rawMetrics as { worst_disparate_impact_ratio: number | null; worst_statistical_parity_difference: number | null };
                      return (
                      <div key={colPair} className="flex flex-col gap-2 p-4 bg-warm-50 rounded-xl border border-warm-100">
                        <span className="text-[12px] font-bold text-warm-600 tracking-wide uppercase break-words">{colPair.replace(/\./g, " × ")}</span>
                        
                        <div className="flex justify-between items-center mt-2">
                          <span className="text-[12px] text-warm-500">Worst DIR</span>
                          <span className="text-[14px] font-bold metric-value text-danger-600">{metrics.worst_disparate_impact_ratio !== null && metrics.worst_disparate_impact_ratio !== undefined ? metrics.worst_disparate_impact_ratio?.toFixed(4) : "N/A"}</span>
                        </div>
                        
                        <div className="flex justify-between items-center">
                          <span className="text-[12px] text-warm-500">Worst SPD</span>
                          <span className="text-[14px] font-bold metric-value text-danger-600">{metrics.worst_statistical_parity_difference !== null && metrics.worst_statistical_parity_difference !== undefined ? metrics.worst_statistical_parity_difference?.toFixed(4) : "N/A"}</span>
                        </div>
                      </div>
                    )})}
                  </div>
                </div>
              )}

              {/* Findings */}
              {Array.isArray(report.findings) && report.findings.length > 0 && (
                <div className="gs-card p-6">
                  <h3 className="text-[14px] font-semibold text-warm-800 mb-4 uppercase tracking-wide border-b border-warm-100 pb-2">Findings</h3>
                  <div className="space-y-3">
                    {report.findings.map((f: string, i: number) => (
                      <div key={i} className="p-3 bg-warning-50 border border-warning-100 rounded-xl text-[13px] text-warning-800">{f}</div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {Array.isArray(report.recommendations) && report.recommendations.length > 0 && (
                <div className="gs-card p-6">
                  <h3 className="text-[14px] font-semibold text-warm-800 mb-4 uppercase tracking-wide border-b border-warm-100 pb-2">Recommendations</h3>
                  <div className="space-y-3">
                    {report.recommendations.map((r: string, i: number) => (
                      <div key={i} className="p-3 bg-success-50 border border-success-100 rounded-xl text-[13px] text-success-800">{r}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
