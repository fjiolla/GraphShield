"use client";

import React, { useMemo, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { useGraphModelStore } from "@/stores/useGraphModelStore";
import { ReactFlowProvider, type Node, type Edge } from "reactflow";
import { DropZone } from "@/components/ui/DropZone";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ScorecardViewer } from "@/components/fairness/ScorecardViewer";
import { ExplainabilityPanel } from "@/components/fairness/ExplainabilityPanel";
import { RemediationPanel } from "@/components/fairness/RemediationPanel";
import { NarrativeSection } from "@/components/fairness/NarrativeSection";
import { DAGCanvas } from "@/components/graph/DAGCanvas";
import { Check, ChevronRight, ChevronLeft, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/utils/cn";

type GraphFormat = "gml" | "csv" | "jsonld";

const STEPS = [
  { id: 1, title: "Graph Data" },
  { id: 2, title: "Model Config" },
  { id: 3, title: "Processing" },
  { id: 4, title: "Report" },
];

function WizardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const step = parseInt(searchParams.get("step") || "1", 10);
  
  const { formData, updateFormData, analyze, result, error, reset } = useGraphModelStore();

  const setStep = (newStep: number) => {
    router.push(`?step=${newStep}`);
  };

  const handleNext = () => setStep(Math.min(step + 1, 4));
  const handlePrev = () => setStep(Math.max(step - 1, 1));

  const handleStartAudit = async () => {
    setStep(3);
    await analyze();
    // Read error from store synchronously after the await resolves
    const { error: auditError } = useGraphModelStore.getState();
    if (auditError) {
      setStep(2); // Return to config step so user can see the error and retry
    } else {
      setStep(4);
    }
  };

  const renderStepper = () => (
    <div className="flex items-center justify-between mb-8 max-w-3xl mx-auto">
      {STEPS.map((s, i) => (
        <React.Fragment key={s.id}>
          <div className="flex flex-col items-center">
            <div
              className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-[13px] font-bold transition-colors",
                step === s.id ? "bg-sage-500 text-white shadow-card" : 
                step > s.id ? "bg-success-500 text-white" : "bg-warm-100 text-warm-400"
              )}
            >
              {step > s.id ? <Check className="w-4 h-4" /> : s.id}
            </div>
            <span className={cn(
              "text-[11px] font-medium mt-2 uppercase tracking-wide",
              step >= s.id ? "text-warm-800" : "text-warm-400"
            )}>
              {s.title}
            </span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={cn(
              "flex-1 h-0.5 mx-4 transition-colors",
              step > s.id ? "bg-success-500" : "bg-warm-100"
            )} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const initialNodes = useMemo<Node[]>(() => {
    if (!result?.scorecard?.universal_metrics) return [];
    return [
      { id: "root", type: "group", position: { x: 250, y: 0 }, data: { label: "Full Graph", size: result.scorecard.graph_metadata.node_count } },
      { id: "m1", type: "metric", position: { x: 50, y: 150 }, data: { label: "Demographic Parity", value: result.scorecard.universal_metrics.demographic_parity.score || 0, status: result.scorecard.universal_metrics.demographic_parity.status } },
      { id: "m2", type: "metric", position: { x: 300, y: 150 }, data: { label: "Equalized Odds", value: result.scorecard.universal_metrics.equalized_odds.score || 0, status: result.scorecard.universal_metrics.equalized_odds.status } },
      { id: "m3", type: "metric", position: { x: 550, y: 150 }, data: { label: "Disparate Impact", value: result.scorecard.universal_metrics.disparate_impact.score || 0, status: result.scorecard.universal_metrics.disparate_impact.status } },
    ];
  }, [result]);

  const initialEdges = useMemo<Edge[]>(() => {
    if (!result?.scorecard?.universal_metrics) return [];
    return [
      { id: "e1", source: "root", target: "m1", animated: true, style: { stroke: 'var(--color-warm-300)' } },
      { id: "e2", source: "root", target: "m2", animated: true, style: { stroke: 'var(--color-warm-300)' } },
      { id: "e3", source: "root", target: "m3", animated: true, style: { stroke: 'var(--color-warm-300)' } },
    ];
  }, [result]);

  return (
    <PageWrapper>
      <PageHeader 
        title="Graph Model Audit Wizard" 
        description="Comprehensive evaluation of topological and predictive biases."
        actions={
          step === 4 && (
            <Button variant="outline" size="sm" onClick={() => { reset(); setStep(1); }}>
              Start New Audit
            </Button>
          )
        }
      />

      {renderStepper()}

      <div className="max-w-4xl mx-auto mt-8">
        {error && step !== 3 && (
          <div className="mb-6 p-4 bg-danger-50 text-danger-600 rounded-xl text-[13px] border border-danger-100">
            {error}
          </div>
        )}

        {step === 1 && (
          <div className="gs-card p-6 md:p-8 animate-fade-in space-y-6">
            <h3 className="font-display text-lg text-warm-800 border-b border-warm-100 pb-2">
              Primary Graph Network
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-[13px] font-semibold text-warm-800 mb-1.5 block">Graph File *</label>
                <DropZone
                  onFileSelect={(f) => updateFormData({ graphFile: f })}
                  selectedFile={formData.graphFile}
                  onClear={() => updateFormData({ graphFile: undefined })}
                  accept={{
                    "application/octet-stream": [".gml"],
                    "text/csv": [".csv"],
                    "application/ld+json": [".jsonld", ".json"],
                  }}
                />
              </div>

              <div>
                <label className="text-[13px] font-semibold text-warm-800 mb-1.5 block">Format *</label>
                <select
                  className="w-full text-[14px] p-3 rounded-xl border border-warm-200 bg-surface focus:ring-2 focus:ring-sage-500/30"
                  value={formData.format || "gml"}
                  onChange={(e) => updateFormData({ format: e.target.value as GraphFormat })}
                >
                  <option value="gml">GML (Graph Modeling Language)</option>
                  <option value="csv">CSV (Edge List)</option>
                  <option value="jsonld">JSON-LD</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <Button onClick={handleNext} disabled={!formData.graphFile}>
                Next Step <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="gs-card p-6 md:p-8 animate-fade-in space-y-6">
            <h3 className="font-display text-lg text-warm-800 border-b border-warm-100 pb-2">
              Model Configuration
            </h3>
            
            <div className="space-y-5">
              <div>
                <label className="text-[13px] font-semibold text-warm-800 mb-1.5 block">Protected Attribute Column *</label>
                <input
                  type="text"
                  className="w-full text-[14px] p-3 rounded-xl border border-warm-200 bg-surface focus:ring-2 focus:ring-sage-500/30"
                  placeholder="e.g. gender, race, age_group"
                  value={formData.protectedAttr || ""}
                  onChange={(e) => updateFormData({ protectedAttr: e.target.value })}
                />
              </div>

              <div>
                <label className="text-[13px] font-semibold text-warm-800 mb-1.5 block">Prediction Source *</label>
                <select
                  className="w-full text-[14px] p-3 rounded-xl border border-warm-200 bg-surface focus:ring-2 focus:ring-sage-500/30"
                  value={formData.predictionSource || "node_attribute"}
                  onChange={(e) => updateFormData({ predictionSource: e.target.value })}
                >
                  <option value="node_attribute">Node Attribute (In-Graph)</option>
                  <option value="csv">External CSV</option>
                  <option value="model_inference">External ML Model (.pkl)</option>
                </select>
              </div>

              {formData.predictionSource === "csv" && (
                <div className="p-4 bg-warm-50 rounded-xl border border-warm-100 space-y-4">
                  <DropZone
                    label="Upload Predictions CSV"
                    onFileSelect={(f) => updateFormData({ predictionsCsv: f })}
                    selectedFile={formData.predictionsCsv}
                    onClear={() => updateFormData({ predictionsCsv: undefined })}
                    accept={{ "text/csv": [".csv"] }}
                    className="p-4 bg-white"
                  />
                </div>
              )}
            </div>

            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={handlePrev}>
                <ChevronLeft className="w-4 h-4" /> Back
              </Button>
              <Button onClick={handleStartAudit} disabled={!formData.protectedAttr || !formData.predictionSource}>
                Run Full Audit
              </Button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="h-full min-h-[400px] gs-card p-8 flex flex-col items-center justify-center text-center space-y-6 animate-fade-in">
             <div className="relative w-24 h-24">
                <div className="absolute inset-0 border-4 border-sage-100 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-sage-500 rounded-full border-t-transparent animate-spin"></div>
             </div>
             <div>
               <h3 className="font-display text-xl text-warm-800 mb-2">Executing Pipeline...</h3>
               <p className="text-[14px] text-warm-500 max-w-sm mx-auto">
                 Calculating graph structural metrics, universal fairness algorithms, and compiling AI narrative report...
               </p>
             </div>
          </div>
        )}

        {step === 4 && result && (
          <div className="space-y-8 animate-fade-in">
            {/* Warnings Banner */}
            {result.warnings && result.warnings.length > 0 && (
              <div className="p-4 bg-warning-50 border border-warning-200 rounded-xl space-y-2">
                {result.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2 text-[13px] text-warning-700">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            )}

            <ScorecardViewer scorecard={result.scorecard} />

            {/* Key Findings + Risk Groups */}
            {(result.scorecard.key_findings.length > 0 || result.scorecard.top_risk_groups.length > 0) && (
              <div className="grid md:grid-cols-2 gap-6">
                {result.scorecard.key_findings.length > 0 && (
                  <div className="gs-card p-6">
                    <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
                      Key Findings
                    </h3>
                    <ul className="space-y-2">
                      {result.scorecard.key_findings.map((f, i) => (
                        <li key={i} className="flex items-start gap-2 text-[13px] text-warm-700">
                          <Info className="w-4 h-4 mt-0.5 text-sage-500 flex-shrink-0" />
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {result.scorecard.top_risk_groups.length > 0 && (
                  <div className="gs-card p-6">
                    <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
                      Top Risk Groups
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {result.scorecard.top_risk_groups.map((g, i) => (
                        <Badge key={i} level="fail">{g}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Global Explanation */}
            {result.scorecard.global_explanation && result.scorecard.global_explanation.top_bias_drivers.length > 0 && (
              <ExplainabilityPanel explanation={result.scorecard.global_explanation} />
            )}

            <div className="grid md:grid-cols-2 gap-6">
              <div className="gs-card p-6">
                 <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
                   Network Visualization
                 </h3>
                 <ReactFlowProvider>
                   <DAGCanvas initialNodes={initialNodes} initialEdges={initialEdges} />
                 </ReactFlowProvider>
              </div>
              <div className="space-y-6">
                <NarrativeSection narrative={[
                  { title: "Fairness Summary", content: result.gemini_report.summary },
                  { title: "Bias Found", content: result.gemini_report.bias_found },
                  { title: "Likely Causes", content: result.gemini_report.likely_causes },
                  { title: "Regulatory Note", content: result.gemini_report.regulatory_note },
                ].filter(n => n.content)} />
                <RemediationPanel plan={[
                  { priority: result.gemini_report.severity_assessment, action: "Address Structural Bias", description: result.gemini_report.remediation, steps: ["Review structural disparity", "Implement corrective model features"] }
                ]} />
              </div>
            </div>
          </div>
        )}
      </div>
    </PageWrapper>
  );
}

export default function GraphModelAuditWizard() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-warm-500">Loading wizard...</div>}>
      <WizardContent />
    </Suspense>
  );
}
