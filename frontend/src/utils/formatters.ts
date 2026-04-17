import { format, formatDistanceToNow, parseISO } from "date-fns";

/** Format ISO timestamp → "Apr 14, 2026" */
export function formatDate(iso: string): string {
  try {
    return format(parseISO(iso), "MMM d, yyyy");
  } catch {
    return iso;
  }
}

/** Format ISO timestamp → "Apr 14, 2026 · 3:45 PM" */
export function formatDateTime(iso: string): string {
  try {
    return format(parseISO(iso), "MMM d, yyyy · h:mm a");
  } catch {
    return iso;
  }
}

/** Format ISO timestamp → "2 hours ago" */
export function formatRelative(iso: string): string {
  try {
    return formatDistanceToNow(parseISO(iso), { addSuffix: true });
  } catch {
    return iso;
  }
}

/** Format number → "1,234" */
export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

/** Format float → "0.4333" (4 decimal places) */
export function formatMetric(n: number, decimals = 4): string {
  return n.toFixed(decimals);
}

/** Format score → "82 / 100" */
export function formatScore(score: number): string {
  return `${Math.round(score)} / 100`;
}

/** Format a percentage → "75.0%" */
export function formatPercent(ratio: number): string {
  return `${(ratio * 100).toFixed(1)}%`;
}

/** Format bytes → "1.2 MB" */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/** Format seconds → "1m 05s" */
export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m === 0) return `${s}s`;
  return `${m}m ${s.toString().padStart(2, "0")}s`;
}
