"use client";
/** RiskBadge – colored badge indicating risk severity. */
import { useStore } from "@/store";

type Severity = "high" | "medium" | "low";
interface Props { severity: Severity; label?: string; }

const COLORS: Record<Severity, string> = {
  high:   "bg-red-100 text-red-700 border-red-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low:    "bg-green-100 text-green-700 border-green-200",
};

const ICONS: Record<Severity, string> = { high: "🔴", medium: "🟡", low: "🟢" };

export default function RiskBadge({ severity, label }: Props) {
  const t = useStore((s) => s.t);
  const key = `risk_${severity}` as any;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${COLORS[severity]}`}>
      {ICONS[severity]} {label || t(key)}
    </span>
  );
}
