"use client";

import React from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { DropZone } from "@/components/ui/DropZone";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useAuditStore } from "@/stores/useAuditStore";
import { AlertCircle, FileText } from "lucide-react";
import { RemediationPanel } from "@/components/fairness/RemediationPanel";
import type { RemediationStep } from "@/types/fairness";

export default function DocumentAuditPage() {
  const { file, setFile, ingest, isLoading, result, error, reset } = useAuditStore();

  return (
    <PageWrapper>
      <PageHeader 
        title="Document Bias Audit" 
        description="Upload text documents (PDF, DOCX, TXT) to scan for demographic and implicit bias."
        actions={
          result && (
            <Button variant="outline" size="sm" onClick={reset}>
              Start New Audit
            </Button>
          )
        }
      />

      <div className="grid lg:grid-cols-12 gap-8">
        <div className="lg:col-span-4 space-y-6">
          <div className="gs-card p-6">
            <h3 className="text-[14px] font-semibold text-warm-800 mb-4 uppercase tracking-wide border-b border-warm-100 pb-2">
              Upload Document
            </h3>
            <DropZone
              onFileSelect={setFile}
              selectedFile={file}
              onClear={() => setFile(null)}
              accept={{
                "application/pdf": [".pdf"],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                "text/plain": [".txt"]
              }}
              disabled={isLoading || !!result}
            />
            {error && (
              <div className="mt-4 p-3 bg-danger-50 text-danger-600 rounded-xl text-[13px] flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p>{error}</p>
              </div>
            )}
            <Button
              className="w-full mt-6"
              size="lg"
              onClick={ingest}
              disabled={!file || isLoading || !!result}
              loading={isLoading}
            >
              Analyze Document
            </Button>
          </div>

          {result && (
            <div className="gs-card p-6">
              <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
                Audit Metadata
              </h3>
              <div className="space-y-4 text-[13px]">
                <div className="flex justify-between">
                  <span className="text-warm-500">File Processed</span>
                  <span className="font-medium text-warm-800 truncate max-w-[150px]" title={result.filename}>
                    {result.filename}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-warm-500">Total Entities</span>
                  <span className="font-medium text-warm-800 metric-value">
                    {result.findings.qualitative_analysis.metadata.total_entities}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-warm-500">Complexity</span>
                  <Badge level="neutral">
                    {result.findings.qualitative_analysis.metadata.document_complexity}
                  </Badge>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-8">
          {!result && !isLoading && (
             <div className="h-full min-h-[400px] border-2 border-dashed border-warm-200 rounded-2xl flex flex-col items-center justify-center text-center p-8">
               <div className="w-16 h-16 rounded-2xl bg-warm-100 text-warm-400 flex items-center justify-center mb-4">
                 <FileText className="w-8 h-8" />
               </div>
               <h3 className="text-lg font-semibold text-warm-800 mb-2">Awaiting Document</h3>
               <p className="text-sm text-warm-500 max-w-sm">
                 Upload a document and click &ldquo;Analyze&rdquo; to extract bias metrics, severity insights, and remediation plans.
               </p>
             </div>
          )}

          {isLoading && (
            <div className="h-full min-h-[400px] gs-card p-8 flex flex-col items-center justify-center text-center space-y-6">
              <div className="relative w-20 h-20">
                 <div className="absolute inset-0 border-4 border-sage-100 rounded-full"></div>
                 <div className="absolute inset-0 border-4 border-sage-500 rounded-full border-t-transparent animate-spin"></div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-warm-800 mb-1">Scanning Document</h3>
                <p className="text-sm text-warm-500">
                  Running NLP models to detect implicit and explicit bias...
                </p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-6 animate-fade-in">
              {/* Verdict Summary Panel */}
              <div className="gs-card p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div>
                  <h2 className="font-display text-xl text-warm-800 mb-2">
                    Analysis Complete
                  </h2>
                  <p className="text-[14px] text-warm-500 max-w-2xl">
                    {result.findings.qualitative_analysis.dynamic_profile.summary.notes}
                  </p>
                </div>
                <div className="flex-shrink-0 text-center bg-warm-50 px-6 py-4 rounded-xl border border-warm-100 w-full md:w-auto">
                    <p className="text-[11px] font-bold text-warm-500 uppercase tracking-widest mb-2">Overall Risk</p>
                    <Badge 
                      level={
                        result.findings.qualitative_analysis.dynamic_profile.summary.overall_bias === "high" 
                        ? "fail" : result.findings.qualitative_analysis.dynamic_profile.summary.overall_bias === "medium" 
                        ? "warn" : "pass"
                      } 
                      className="px-4 py-1.5 text-sm"
                    >
                      {result.findings.qualitative_analysis.dynamic_profile.summary.overall_bias}
                    </Badge>
                </div>
              </div>

              {/* Detected Groups */}
              <h3 className="font-display text-lg text-warm-800 mt-8 mb-4 border-b border-warm-100 pb-2">
                Flagged Demographics
              </h3>
              <div className="grid sm:grid-cols-2 gap-4">
                {result.findings.qualitative_analysis.dynamic_profile.groups.map((group, idx) => (
                  <div key={idx} className="gs-card p-5 border-l-4 border-l-warning-500">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-warm-800">{group.group_name}</h4>
                      <Badge level={group.bias_type === "explicit" ? "fail" : "warn"}>
                        {group.bias_type}
                      </Badge>
                    </div>
                    <p className="text-[13px] text-warm-600 mb-3">{group.justification}</p>
                    <div className="flex gap-2 flex-wrap">
                      {group.descriptors.slice(0,3).map((d, i) => (
                        <span key={i} className="text-[11px] bg-warm-100 text-warm-600 px-2 py-1 rounded">
                          &quot;{d}&quot;
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Quantitative Verification — FIX: was missing */}
              {result.findings.quantitative_verification && result.findings.quantitative_verification.length > 0 && (
                <>
                  <h3 className="font-display text-lg text-warm-800 mt-8 mb-4 border-b border-warm-100 pb-2">
                    Quantitative Verification
                  </h3>
                  <div className="gs-card overflow-hidden">
                    <table className="w-full text-[13px]">
                      <thead>
                        <tr className="border-b border-warm-100">
                          <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-warm-400">Group</th>
                          <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-warm-400">Proximity Score</th>
                          <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-warm-400">Evidence Count</th>
                          <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-warm-400">Weight</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.findings.quantitative_verification.map((v, i) => (
                          <tr key={i} className="border-b border-warm-50 last:border-0">
                            <td className="px-4 py-3 font-medium text-warm-800">{v.group}</td>
                            <td className="px-4 py-3 metric-value">{v.contextual_proximity_score.toFixed(4)}</td>
                            <td className="px-4 py-3 metric-value">{v.evidence_count}</td>
                            <td className="px-4 py-3">
                              <Badge level={v.mathematical_weight === "Strong" ? "fail" : "warn"}>
                                {v.mathematical_weight}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {/* Remediation Plan */}
              {result.recommendation?.remediation_plan && (Array.isArray(result.recommendation.remediation_plan) ? result.recommendation.remediation_plan.length > 0 : Object.keys(result.recommendation.remediation_plan).length > 0) && (
                <>
                  <h3 className="font-display text-lg text-warm-800 mt-8 mb-4 border-b border-warm-100 pb-2">
                    Action Plan
                  </h3>
                  <RemediationPanel 
                    plan={
                      Array.isArray(result.recommendation.remediation_plan) 
                        ? result.recommendation.remediation_plan 
                        : Object.entries(result.recommendation.remediation_plan).map(([k, v]: [string, unknown]) => {
                          const val = v as Record<string, unknown> | string;
                          return {
                            priority: "HIGH" as const,
                            action: k,
                            description: typeof val === "object" && val !== null ? String((val as Record<string, unknown>).description || val) : String(val),
                            steps: typeof val === "object" && val !== null && Array.isArray((val as Record<string, unknown>).steps) 
                              ? (val as Record<string, string[]>).steps 
                              : [String(val)]
                          } satisfies RemediationStep;
                        })
                    } 
                  />
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
