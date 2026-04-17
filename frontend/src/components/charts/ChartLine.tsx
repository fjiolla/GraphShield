"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { cn } from "@/utils/cn";

interface ChartLineProps {
  data: Record<string, unknown>[];
  xKey: string;
  lines: { key: string; color: string; label?: string }[];
  height?: number;
  title?: string;
  className?: string;
}

export function ChartLine({
  data,
  xKey,
  lines,
  height = 280,
  title,
  className,
}: ChartLineProps) {
  return (
    <div className={cn("gs-card p-5", className)}>
      {title && (
        <p className="text-[13px] font-semibold text-warm-700 mb-4">{title}</p>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E8E6E0" vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 11, fill: "#A8A6A0" }}
            axisLine={{ stroke: "#E8E6E0" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#A8A6A0" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "#fff",
              border: "none",
              borderRadius: "12px",
              boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
              fontSize: "12px",
            }}
          />
          {lines.length > 1 && (
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
            />
          )}
          {lines.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              stroke={line.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
              name={line.label || line.key}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
