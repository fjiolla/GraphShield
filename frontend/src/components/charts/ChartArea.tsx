"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { cn } from "@/utils/cn";

interface ChartAreaProps {
  data: Record<string, unknown>[];
  xKey: string;
  areaKey: string;
  height?: number;
  title?: string;
  color?: string;
  className?: string;
}

export function ChartArea({
  data,
  xKey,
  areaKey,
  height = 240,
  title,
  color = "#4D6B44",
  className,
}: ChartAreaProps) {
  return (
    <div className={cn("gs-card p-5", className)}>
      {title && (
        <p className="text-[13px] font-semibold text-warm-700 mb-4">{title}</p>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
          <defs>
            <linearGradient id={`areaGrad-${areaKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.2} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
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
          <Area
            type="monotone"
            dataKey={areaKey}
            stroke={color}
            strokeWidth={2}
            fill={`url(#areaGrad-${areaKey})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
