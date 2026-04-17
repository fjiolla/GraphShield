"use client";

import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { cn } from "@/utils/cn";

interface DonutSegment {
  name: string;
  value: number;
  color: string;
}

interface ChartDonutProps {
  data: DonutSegment[];
  height?: number;
  title?: string;
  centerLabel?: string;
  centerValue?: string;
  className?: string;
}

export function ChartDonut({
  data,
  height = 240,
  title,
  centerLabel,
  centerValue,
  className,
}: ChartDonutProps) {
  return (
    <div className={cn("gs-card p-5", className)}>
      {title && (
        <p className="text-[13px] font-semibold text-warm-700 mb-4">{title}</p>
      )}
      <div className="relative">
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "#fff",
                border: "none",
                borderRadius: "12px",
                boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
                fontSize: "12px",
              }}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Center label */}
        {centerValue && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-xl font-semibold text-warm-800 metric-value">
              {centerValue}
            </span>
            {centerLabel && (
              <span className="text-[11px] text-warm-400">{centerLabel}</span>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-2 justify-center">
        {data.map((entry, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-[11px] text-warm-500">{entry.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
