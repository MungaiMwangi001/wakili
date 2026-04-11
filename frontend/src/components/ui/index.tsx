// src/components/ui/index.tsx
// Reusable UI primitives used throughout Wakili.

"use client";

import { motion } from "framer-motion";
import { clsx } from "clsx";
import { AlertTriangle, CheckCircle, AlertCircle } from "lucide-react";

// ── Card ─────────────────────────────────────────────────────────────────────

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={clsx("bg-bg-card rounded-xl2 shadow-card p-6", className)}
    >
      {children}
    </motion.div>
  );
}

// ── RiskBadge ─────────────────────────────────────────────────────────────────

type Severity = "high" | "medium" | "low";

const severityConfig: Record<Severity, { label: string; cls: string; Icon: typeof AlertTriangle }> = {
  high:   { label: "High",   cls: "risk-high",   Icon: AlertTriangle },
  medium: { label: "Medium", cls: "risk-medium",  Icon: AlertCircle },
  low:    { label: "Low",    cls: "risk-low",     Icon: CheckCircle },
};

export function RiskBadge({ severity }: { severity: Severity }) {
  const { label, cls, Icon } = severityConfig[severity] ?? severityConfig.medium;
  return (
    <span className={clsx("inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full", cls)}>
      <Icon size={12} />
      {label}
    </span>
  );
}

// ── ClauseHighlight ───────────────────────────────────────────────────────────

interface ClauseHighlightProps {
  number: number;
  title: string;
  summary: string;
  hasRisk?: boolean;
  riskSeverity?: Severity;
  onClick?: () => void;
}

export function ClauseHighlight({ number, title, summary, hasRisk, riskSeverity = "low", onClick }: ClauseHighlightProps) {
  return (
    <motion.div
      whileHover={{ x: 4 }}
      onClick={onClick}
      className={clsx(
        "border-l-4 pl-4 py-3 cursor-pointer rounded-r-lg transition-colors",
        hasRisk ? "border-primary bg-highlight/40" : "border-accent bg-bg-panel/30"
      )}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-mono text-primary/70">§{number}</span>
        {hasRisk && <RiskBadge severity={riskSeverity} />}
      </div>
      <p className="font-display font-semibold text-sm text-gray-800">{title}</p>
      <p className="text-xs text-gray-600 mt-1 line-clamp-2">{summary}</p>
    </motion.div>
  );
}

// ── ChatBubble ────────────────────────────────────────────────────────────────

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  language?: string;
}

export function ChatBubble({ role, content, language }: ChatBubbleProps) {
  const isUser = role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx("flex", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-xs font-bold mr-2 shrink-0">
          W
        </div>
      )}
      <div
        className={clsx(
          "max-w-[78%] px-4 py-3 rounded-2xl text-sm leading-relaxed",
          isUser
            ? "bg-primary text-white rounded-br-sm"
            : "bg-bg-card shadow-card text-gray-800 rounded-bl-sm"
        )}
      >
        {content}
        {language && (
          <span className="block text-[10px] opacity-60 mt-1">
            {language === "sw" ? "Kiswahili" : "English"}
          </span>
        )}
      </div>
    </motion.div>
  );
}

// ── AnalyticsCard ─────────────────────────────────────────────────────────────

interface AnalyticsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: "primary" | "accent" | "analytics" | "panel";
  icon?: React.ReactNode;
}

const colorMap = {
  primary:   "bg-primary text-white",
  accent:    "bg-accent text-gray-900",
  analytics: "bg-bg-analytics text-gray-800",
  panel:     "bg-bg-panel text-gray-800",
};

export function AnalyticsCard({ title, value, subtitle, color = "analytics", icon }: AnalyticsCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={clsx("rounded-xl2 p-5 shadow-card", colorMap[color])}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium opacity-70 uppercase tracking-wider">{title}</p>
          <p className="font-display text-3xl font-bold mt-1">{value}</p>
          {subtitle && <p className="text-xs opacity-60 mt-1">{subtitle}</p>}
        </div>
        {icon && <div className="opacity-80">{icon}</div>}
      </div>
    </motion.div>
  );
}

// ── UploadZone ────────────────────────────────────────────────────────────────

import { useDropzone } from "react-dropzone";
import { Upload } from "lucide-react";

interface UploadZoneProps {
  onDrop: (files: File[]) => void;
  uploading?: boolean;
  hint?: string;
}

export function UploadZone({ onDrop, uploading = false, hint }: UploadZoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    multiple: false,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "border-2 border-dashed rounded-xl2 p-10 text-center cursor-pointer transition-all duration-200",
        isDragActive
          ? "border-primary bg-highlight/30 scale-[1.01]"
          : "border-primary/30 hover:border-primary hover:bg-bg-panel/30",
        uploading && "opacity-50 cursor-not-allowed"
      )}
    >
      <input {...getInputProps()} />
      <motion.div
        animate={uploading ? { rotate: 360 } : {}}
        transition={uploading ? { repeat: Infinity, duration: 1.5, ease: "linear" } : {}}
        className="inline-block mb-3"
      >
        <Upload size={36} className="text-primary mx-auto" />
      </motion.div>
      <p className="text-sm text-gray-600 font-medium">
        {uploading ? "Uploading…" : isDragActive ? "Drop it here!" : hint || "Drag & drop or click to upload"}
      </p>
      <p className="text-xs text-gray-400 mt-1">PDF, DOCX, TXT · Max 50 MB</p>
    </div>
  );
}
