"use client";

import React from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  NodeChange,
  EdgeChange
} from "reactflow";
import "reactflow/dist/style.css";
import MetricNode from "./nodes/MetricNode";
import GroupNode from "./nodes/GroupNode";

const nodeTypes = {
  metric: MetricNode,
  group: GroupNode,
};

interface DAGCanvasProps {
  initialNodes: Node[];
  initialEdges: Edge[];
}

export function DAGCanvas({ initialNodes, initialEdges }: DAGCanvasProps) {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  // NOTE: ReactFlowProvider must be wrapped at the parent page level!
  return (
    <div className="h-[400px] w-full border border-warm-200 rounded-2xl overflow-hidden bg-white/50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange as (changes: NodeChange[]) => void}
        onEdgesChange={onEdgesChange as (changes: EdgeChange[]) => void}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="var(--color-warm-300)" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap 
          nodeColor={(n) => {
            if (n.type === 'metric') return '#F5E0DB';
            return '#EAF0E8';
          }}
          maskColor="rgba(245, 244, 240, 0.6)"
        />
      </ReactFlow>
    </div>
  );
}
