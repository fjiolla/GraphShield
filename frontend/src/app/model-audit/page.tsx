"use client";

import React from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { DropZone } from "@/components/ui/DropZone";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useModelAuditStore } from "@/stores/useModelAuditStore";
import { AlertCircle, Target, Combine } from "lucide-react";
import { VerdictBadge } from "@/components/fairness/VerdictBadge";
import { FairnessScorePanel } from "@/components/fairness/FairnessScorePanel";
import { RemediationPanel } from "@/components/fairness/RemediationPanel";
import { NarrativeSection } from "@/components/fairness/NarrativeSection";
import { StatCard } from "@/components/ui/StatCard";

export default function ModelAuditPage() {
  const { modelFile, datasetFile, setModelFile, setDatasetFile, runAudit, isLoading, result, error, reset } = useModelAuditStore();

  const handleStart = () => {
    runAudit();
  };

  return (
    <PageWrapper>
      <PageHeader 
        title="ML Model Fairness Audit" 
        description="Upload a trained model (.pkl, .joblib) and its training/test dataset to evaluate bias across protected groups."
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
              Audit Inputs
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-[12px] font-semibold text-warm-700 mb-1.5 block">Trained Model (.pkl / .joblib)</label>
                <DropZone
                  onFileSelect={setModelFile}
                  selectedFile={modelFile}
                  onClear={() => setModelFile(null)}
                  disabled={isLoading || !!result}
                  className="p-4"
                  accept={{ "application/octet-stream": [".pkl", ".joblib", ".pt"] }}
                />
              </div>

              <div>
                <label className="text-[12px] font-semibold text-warm-700 mb-1.5 block">Dataset (.csv with ground truth)</label>
                <DropZone
                  onFileSelect={setDatasetFile}
                  selectedFile={datasetFile}
                  onClear={() => setDatasetFile(null)}
                  disabled={isLoading || !!result}
                  className="p-4"
                  accept={{ "text/csv": [".csv"] }}
                />
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-danger-50 text-danger-600 rounded-xl text-[13px] flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p>{error}</p>
              </div>
            )}

            <Button
              className="w-full mt-6"
              size="lg"
              onClick={handleStart}
              disabled={!modelFile || !datasetFile || isLoading || !!result}
              loading={isLoading}
            >
              Analyze Model Pipeline
            </Button>
          </div>

          {result && result.auto_detected && (
            <div className="gs-card p-6">
              <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
                Auto-Detected Schema
              </h3>
              <div className="space-y-4 text-[13px]">
                <div className="flex justify-between items-center">
                  <span className="text-warm-500">Model Type</span>
                  <Badge level="neutral">{result.auto_detected.model_type_detected}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-warm-500">Protected</span>
                  <Badge level="warn">{result.auto_detected.selected_protected_column}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-warm-500">Target</span>
                  <Badge level="info">{result.auto_detected.selected_target_column}</Badge>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-8">
          {!result && !isLoading && (
             <div className="h-full min-h-[400px] border-2 border-dashed border-warm-200 rounded-2xl flex flex-col items-center justify-center text-center p-8">
               <div className="w-16 h-16 rounded-2xl bg-warm-100 text-warm-400 flex items-center justify-center mb-4">
                 <Combine className="w-8 h-8" />
               </div>
               <h3 className="font-display text-lg text-warm-800 mb-2">Dual Upload Required</h3>
               <p className="text-sm text-warm-500 max-w-sm">
                 Upload both the trained model file and the dataset to uncover disparate impact, equal opportunity, and compute SHAP feature importance.
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
                <h3 className="font-display text-lg text-warm-800 mb-1">Re-running Predictions</h3>
                <p className="text-sm text-warm-500">
                  Calculating SHAP values and evaluating fairness thresholds. This may take a minute.
                </p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-6 animate-fade-in">
              {/* Top summary row */}
              <div className="grid md:grid-cols-3 gap-6">
                 <div className="md:col-span-1 flex items-stretch">
                   <VerdictBadge 
                     verdict={result.verdict.bias_verdict} 
                     confidence={result.verdict.bias_confidence}
                     className="w-full h-full" 
                   />
                 </div>
                 <div className="md:col-span-2 grid grid-cols-2 gap-4">
                   <StatCard label="Total Predictions" value={result.total_predictions} />
                   <StatCard label="Overall Score" value={result.governance.overall_fairness_score.toFixed(0)} icon={<Target/>} />
                   <StatCard label="Worst Group" value={result.verdict.worst_group} />
                   <StatCard label="Disp. Impact Ratio" value={result.verdict.worst_disparate_impact_ratio.toFixed(3)} />
                 </div>
              </div>

              {/* Metrics Flat Panel */}
              {result.governance.bias_scorecard.length > 0 && (
                <FairnessScorePanel 
                  title="Fairness Metrics Scorecard" 
                  flatScores={result.governance.bias_scorecard}
                />
              )}


              {/* Narrative & Remediation */}
              <NarrativeSection narrative={result.ai_narrative} />
              
              <h3 className="font-display text-lg text-warm-800 mt-8 mb-4 border-b border-warm-100 pb-2">
                Governance & Remediation Plan
              </h3>
              <RemediationPanel plan={result.governance.remediation_plan} />

            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
