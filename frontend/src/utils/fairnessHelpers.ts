/**
 * Map a 0-100 fairness score to a color class name.
 * ≥80 → green (good), 60–79 → amber (moderate), <60 → red (poor)
 */
export function scoreColor(score: number): string {
  if (score >= 80) return "text-success-500";
  if (score >= 60) return "text-warning-500";
  return "text-danger-500";
}

/** Score → background color */
export function scoreBgColor(score: number): string {
  if (score >= 80) return "bg-success-50";
  if (score >= 60) return "bg-warning-50";
  return "bg-danger-50";
}

/** Map PASS/WARN/FAIL status to a color class */
export function statusColor(status: string): string {
  switch (status) {
    case "PASS":
      return "text-success-500";
    case "WARN":
      return "text-warning-700";
    case "FAIL":
      return "text-danger-500";
    default:
      return "text-warm-500";
  }
}

/** Map PASS/WARN/FAIL to a background pill style */
export function statusBgColor(status: string): string {
  switch (status) {
    case "PASS":
      return "bg-success-50 text-success-500";
    case "WARN":
      return "bg-warning-50 text-warning-700";
    case "FAIL":
      return "bg-danger-50 text-danger-500";
    default:
      return "bg-warm-100 text-warm-500";
  }
}

/** Map bias verdict to colors */
export function verdictColor(verdict: string): {
  text: string;
  bg: string;
  border: string;
} {
  switch (verdict) {
    case "BIASED":
      return {
        text: "text-danger-500",
        bg: "bg-danger-50",
        border: "border-danger-500",
      };
    case "MARGINAL":
      return {
        text: "text-warning-700",
        bg: "bg-warning-50",
        border: "border-warning-500",
      };
    case "FAIR":
      return {
        text: "text-success-500",
        bg: "bg-success-50",
        border: "border-success-500",
      };
    default:
      return {
        text: "text-warm-500",
        bg: "bg-warm-100",
        border: "border-warm-300",
      };
  }
}

/** Map severity assessment to icon and color */
export function severityInfo(severity: string): {
  label: string;
  color: string;
  bg: string;
} {
  switch (severity) {
    case "CRITICAL":
      return { label: "Critical", color: "text-danger-500", bg: "bg-danger-50" };
    case "HIGH":
      return { label: "High", color: "text-danger-500", bg: "bg-danger-50" };
    case "MEDIUM":
      return { label: "Medium", color: "text-warning-700", bg: "bg-warning-50" };
    case "LOW":
      return { label: "Low", color: "text-success-500", bg: "bg-success-50" };
    default:
      return { label: severity, color: "text-warm-500", bg: "bg-warm-100" };
  }
}

/** Score → label */
export function scoreLabel(score: number): string {
  if (score >= 80) return "Good";
  if (score >= 60) return "Moderate";
  return "Poor";
}
