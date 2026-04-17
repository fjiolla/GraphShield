import React, { memo } from "react";
import { Handle, Position } from "reactflow";
import { Users } from "lucide-react";

interface GroupNodeData {
  label: string;
  size: number;
}

const GroupNode = memo(({ data }: { data: GroupNodeData }) => {
  return (
    <div className="px-4 py-3 shadow-sm rounded-full bg-sage-50 text-sage-900 border border-sage-200 min-w-[120px] flex items-center justify-center gap-2">
      <Handle type="target" position={Position.Top} className="!bg-sage-300" />
      <Users className="w-4 h-4 text-sage-600" />
      <div className="text-[12px] font-semibold">{data.label}</div>
      <div className="text-[10px] bg-sage-200 px-1.5 py-0.5 rounded-full text-sage-800">{data.size}</div>
      <Handle type="source" position={Position.Bottom} className="!bg-sage-300" />
    </div>
  );
});

GroupNode.displayName = "GroupNode";
export default GroupNode;
