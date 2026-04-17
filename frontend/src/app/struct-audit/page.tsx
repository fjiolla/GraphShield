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
                 <strong>Detected Columns:</strong> {uploadResult.ingestion.columns.join(", ")}
              </div>
            </div>
          )}

          {report && (
            <div className="space-y-6 animate-fade-in">
              <div className="gs-card p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div>
                  <h2 className="font-display text-xl text-warm-800 mb-2">Fairness Report generated</h2>
                  <p className="text-warm-500 text-[14px]">
                    Dataset was evaluated against fairness criteria.
                  </p>
                </div>
                <div className="flex-shrink-0 bg-warm-50 px-6 py-4 rounded-xl border border-warm-100 w-full md:w-auto text-center">
                    <p className="text-[11px] font-bold text-warm-500 uppercase tracking-widest mb-2">Overall Risk</p>
                    <Badge 
                      level={report.risk_level === "High" ? "fail" : report.risk_level === "Medium" ? "warn" : "pass"} 
                      className="px-4 py-1.5 text-sm"
                    >
                      {report.risk_level || "UNKNOWN"}
                    </Badge>
                </div>
              </div>

              <div className="gs-card p-6 bg-surface-alt">
                 <pre className="text-[12px] text-warm-800 overflow-x-auto whitespace-pre-wrap">
                   {JSON.stringify(report, null, 2)}
                 </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
