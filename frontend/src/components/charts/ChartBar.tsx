"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { cn } from "@/utils/cn";

interface BarDataItem {
  name: string;
  value: number;
  color?: string;
}

interface ChartBarProps {
  data: BarDataItem[];
  height?: number;
  title?: string;
  defaultColor?: string;
  layout?: "horizontal" | "vertical";
  className?: string;
}

export function ChartBar({
  data,
  height = 280,
  title,
  defaultColor = "#4D6B44",
  layout = "vertical",
  className,
}: ChartBarProps) {
  return (
    <div className={cn("gs-card p-5", className)}>
      {title && (
        <p className="text-[13px] font-semibold text-warm-700 mb-4">{title}</p>
      )}
      <ResponsiveContainer width="100%" height={height}>
        {layout === "vertical" ? (
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 5, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E8E6E0" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: "#A8A6A0" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11, fill: "#6B6B68" }}
              axisLine={false}
              tickLine={false}
              width={100}
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
            <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color || defaultColor} />
              ))}
            </Bar>
          </BarChart>
        ) : (
          <BarChart data={data} margin={{ top: 0, right: 5, bottom: 0, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E8E6E0" vertical={false} />
            <XAxis
              dataKey="name"
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
            <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={28}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color || defaultColor} />
              ))}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
