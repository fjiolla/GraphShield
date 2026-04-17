import React, { memo } from "react";
import { Handle, Position } from "reactflow";
import { cn } from "@/utils/cn";
import { Gauge } from "lucide-react";

interface MetricNodeData {
  label: string;
  value: number;
  status?: "PASS" | "WARN" | "FAIL";
}

const MetricNode = memo(({ data }: { data: MetricNodeData }) => {
  const isFail = data.status === "FAIL";
  const isWarn = data.status === "WARN";

  return (
    <div
      className={cn(
        "px-4 py-3 shadow-md rounded-xl bg-white border-2 min-w-[140px]",
        isFail ? "border-danger-500" : isWarn ? "border-warning-500" : "border-success-500"
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-warning-300" />
      <div className="flex items-center gap-2 mb-1">
        <Gauge 
          className={cn(
            "w-4 h-4",
            isFail ? "text-danger-500" : isWarn ? "text-warning-500" : "text-success-500"
          )} 
        />
        <div className="text-[10px] uppercase tracking-wider font-semibold text-warm-500">
          {data.label}
        </div>
      </div>
      <div className="text-lg font-bold text-warm-800 metric-value">
        {data.value.toFixed(2)}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-warning-300" />
    </div>
  );
});

MetricNode.displayName = "MetricNode";
export default MetricNode;
