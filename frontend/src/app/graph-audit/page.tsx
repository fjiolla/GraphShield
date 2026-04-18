"use client";

import React from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { DropZone } from "@/components/ui/DropZone";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useGraphStore } from "@/stores/useGraphStore";
import { AlertCircle, Network } from "lucide-react";
import { ExplainabilityPanel } from "@/components/fairness/ExplainabilityPanel";

export default function GraphAuditPage() {
  const { graphFile, nodesFile, config, setGraphFile, setNodesFile, setConfig, analyze, isLoading, result, error, reset } = useGraphStore();

  return (
    <PageWrapper>
      <PageHeader 
        title="Graph Structural Audit" 
        description="Analyze pure network structures (no ML model needed) for inherent topological bias."
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
              Graph Data
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-[12px] font-semibold text-warm-700 mb-1.5 block">Graph Edges File (GML/CSV/JSONLD)</label>
                <DropZone
                  onFileSelect={setGraphFile}
                  selectedFile={graphFile}
                  onClear={() => setGraphFile(null)}
                  disabled={isLoading || !!result}
                  accept={{
                    "application/octet-stream": [".gml"],
                    "text/csv": [".csv"],
                    "application/ld+json": [".jsonld", ".json"],
                  }}
                  className="p-4"
                />
              </div>

              <div>
                <label className="text-[12px] font-semibold text-warm-700 mb-1.5 block">Nodes Metadata (Optional CSV)</label>
                <DropZone
                  onFileSelect={setNodesFile}
                  selectedFile={nodesFile}
                  onClear={() => setNodesFile(null)}
                  disabled={isLoading || !!result}
                  accept={{ "text/csv": [".csv"] }}
                  className="p-4"
                />
              </div>

              <div>
                <label className="text-[12px] font-semibold text-warm-700 mb-1.5 block">Audit Config Override (JSON)</label>
                <textarea
                  className="w-full text-[13px] p-3 rounded-xl border border-warm-200 bg-surface focus:outline-none focus:ring-2 focus:ring-sage-500/30"
                  rows={4}
                  placeholder='{"target_node_types": ["Person"]}'
                  value={config}
                  onChange={(e) => setConfig(e.target.value)}
                  disabled={isLoading || !!result}
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
              onClick={analyze}
              disabled={!graphFile || isLoading || !!result}
              loading={isLoading}
            >
              Analyze Graph Structure
            </Button>
          </div>

          {result && result.graph_metadata && (
            <div className="gs-card p-6">
              <h3 className="text-[14px] font-semibold text-warm-800 mb-4 border-b border-warm-100 pb-2">
                Network Topology
              </h3>
              <div className="space-y-4 text-[13px]">
                <div className="flex justify-between">
                  <span className="text-warm-500">Nodes</span>
                  <span className="font-medium text-warm-800 metric-value">
                    {result.graph_metadata.node_count}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-warm-500">Edges</span>
                  <span className="font-medium text-warm-800 metric-value">
                    {result.graph_metadata.edge_count}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-warm-500">Directed</span>
                  <Badge level={result.graph_metadata.is_directed ? "info" : "neutral"}>
                    {result.graph_metadata.is_directed ? "YES" : "NO"}
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
                 <Network className="w-8 h-8" />
               </div>
               <h3 className="text-lg font-semibold text-warm-800 mb-2">Upload Graph Data</h3>
               <p className="text-sm text-warm-500 max-w-sm">
                 Supply a graph edge list or GML file to uncover topological bias and disparate connectivity.
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
                <h3 className="text-lg font-semibold text-warm-800 mb-1">Traversing Graph...</h3>
                <p className="text-sm text-warm-500">
                  Computing centrality, modularity, and structural disparity metrics.
                </p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-6 animate-fade-in">
              <h3 className="font-display text-lg text-warm-800 mb-4 border-b border-warm-100 pb-2">
                Structural Bias Metrics
              </h3>
              
              <div className="grid sm:grid-cols-2 gap-4">
                 {result.bias_metrics && Object.entries(result.bias_metrics).map(([k, v], i) => {
                    const isObj = typeof v === 'object' && v !== null;
                    const vObj = v as Record<string, unknown>;
                    const isBiased = isObj ? !!vObj.biased : false;
                    
                    let primaryMetricValue: string | number | null = null;
                    let primaryMetricLabel = "Metric";
                    
                    if (isObj) {
                      if (k === "structural_bias") {
                        const ratios = (vObj.disparity_ratios as Record<string, number>) || {};
                        const vals = Object.values(ratios);
                        primaryMetricValue = vals.length > 0 ? Math.min(...vals).toFixed(4) : "N/A";
                        primaryMetricLabel = "Worst Disparity Ratio";
                      } else if (k === "group_fairness") {
                        const di = (vObj.disparate_impact as Record<string, Record<string, unknown>>) || {};
                        const diVals = Object.values(di).map(m => m?.disparate_impact_ratio as number | undefined).filter(x => x !== undefined) as number[];
                        primaryMetricValue = diVals.length > 0 ? Math.min(...diVals).toFixed(4) : "N/A";
                        primaryMetricLabel = "Worst Disparate Impact";
                      } else if (k === "edge_bias") {
                        primaryMetricValue = ((vObj.homophily_index as number) || 0).toFixed(4);
                        primaryMetricLabel = "Homophily Index";
                      } else {
                        primaryMetricValue = "Completed";
                        primaryMetricLabel = "Status";
                      }
                    } else {
                      primaryMetricValue = typeof v === "number" ? v.toFixed(4) : String(v);
                    }

                    return (
                      <div key={i} className={`gs-card p-5 border-l-4 ${isObj ? (isBiased ? 'border-l-danger-500 bg-danger-50/30' : 'border-l-sage-500 bg-sage-50/30') : 'border-l-warm-300'}`}>
                        <div className="flex justify-between items-start mb-4">
                          <p className="text-[12px] font-bold text-warm-600 uppercase tracking-wider">
                            {k.replace(/_/g, " ")}
                          </p>
                          {isObj && (
                            <Badge level={isBiased ? "fail" : "pass"}>
                              {isBiased ? "BIASED" : "FAIR"}
                            </Badge>
                          )}
                        </div>
                        <div>
                           <p className="text-[10px] font-semibold text-warm-500 mb-1 uppercase tracking-wider">{primaryMetricLabel}</p>
                           <p className={`text-2xl font-semibold metric-value ${isBiased ? 'text-danger-700' : 'text-warm-800'}`}>
                             {primaryMetricValue}
                           </p>
                        </div>
                      </div>
                    );
                 })}
                 {(!result.bias_metrics || Object.keys(result.bias_metrics).length === 0) && (
                   <div className="sm:col-span-2 p-6 text-center text-warm-400 bg-warm-50 rounded-xl">
                      No numeric metrics returned by this endpoint algorithm run.
                   </div>
                 )}
              </div>

              {result.explanation && (
                <div className="mt-8">
                  <ExplainabilityPanel explanation={result.explanation} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}
