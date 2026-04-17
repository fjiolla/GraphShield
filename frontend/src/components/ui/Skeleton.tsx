"use client";

import React from "react";
import { cn } from "@/utils/cn";

interface SkeletonProps {
  className?: string;
  lines?: number;
}

export function Skeleton({ className }: SkeletonProps) {
  return <div className={cn("skeleton bg-warm-200", className)} />;
}

/** Pre-built skeleton for a stat card */
export function StatCardSkeleton() {
  return (
    <div className="gs-card-static p-5 space-y-3">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-7 w-28" />
      <Skeleton className="h-3 w-36" />
    </div>
  );
}

/** Pre-built skeleton for a table */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="gs-card-static p-4 space-y-3">
      <Skeleton className="h-4 w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

/** Pre-built skeleton for a chart */
export function ChartSkeleton() {
  return (
    <div className="gs-card-static p-5">
      <Skeleton className="h-4 w-32 mb-4" />
      <Skeleton className="h-48 w-full rounded-xl" />
    </div>
  );
}
