"use client";

import React from "react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { cn } from "@/utils/cn";

interface RadarDataItem {
  metric: string;
  score: number;
  fullMark?: number;
}

interface ChartRadarProps {
  data: RadarDataItem[];
  height?: number;
  title?: string;
  color?: string;
  fillOpacity?: number;
  className?: string;
}

export function ChartRadar({
  data,
  height = 280,
  title,
  color = "#4D6B44",
  fillOpacity = 0.2,
  className,
}: ChartRadarProps) {
  return (
    <div className={cn("gs-card p-5", className)}>
      {title && (
        <p className="text-[13px] font-semibold text-warm-700 mb-4">{title}</p>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#E8E6E0" />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fontSize: 11, fill: "#6B6B68" }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: "#A8A6A0" }}
            axisLine={false}
          />
          <Radar
            dataKey="score"
            stroke={color}
            fill={color}
            fillOpacity={fillOpacity}
            strokeWidth={2}
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
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
