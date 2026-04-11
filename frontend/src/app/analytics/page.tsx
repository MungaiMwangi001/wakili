"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import { 
  FileText, 
  MessageSquare, 
  Zap, 
  Activity, 
  CheckCircle2, 
  AlertCircle, 
  Clock,
  Globe2,
  Database,
  ShieldAlert
} from "lucide-react";
import { metricsApi, documentsApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";

const COLORS = {
  primary: "#977dff",
  secondary: "#02effe",
  accent: "#ffccf2",
  neutral: "#aee1f9",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
};

const PIE_COLORS = [COLORS.primary, COLORS.secondary, COLORS.accent, COLORS.neutral];

interface Metrics {
  documents: { total: number; ready: number; processing: number; errors: number };
  queries:   { total: number; avg_response_ms: number };
  language_breakdown: Record<string, number>;
}

interface RecentDoc {
  id: number;
  title: string;
  filename?: string;
  status: string;
  file_size_bytes: number;
  chunk_count: number;
  detected_language: string | null;
  risk_flags: any[] | null;
}

export default function AnalyticsPage() {
  const [metrics, setMetrics]     = useState<Metrics | null>(null);
  const [recentDocs, setRecentDocs] = useState<RecentDoc[]>([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.all([
      metricsApi.get().then((r) => setMetrics(r.data)).catch(() => {}),
      documentsApi.list().then((r) => setRecentDocs(r.data.slice(0, 5))).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <AppShell>
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
        <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Aggregating Metrics...</p>
      </div>
    </AppShell>
  );

  const totalDocs      = metrics?.documents?.total       ?? 0;
  const totalQueries   = metrics?.queries?.total         ?? 0;
  const avgResponseMs  = Math.round(metrics?.queries?.avg_response_ms ?? 0);
  const isActive       = totalDocs > 0;

  const pieData = Object.entries(metrics?.language_breakdown ?? {}).map(([name, value]) => ({
    name: name === "sw" ? "Swahili" : name === "en" ? "English" : name,
    value,
  }));

  const statusData = metrics ? [
    { label: "Ready",       count: metrics.documents.ready, color: COLORS.success },
    { label: "Processing", count: metrics.documents.processing, color: COLORS.warning },
    { label: "Errors",      count: metrics.documents.errors, color: COLORS.danger },
  ] : [];

  const kpis = [
    { label: "Documents",   value: totalDocs,      icon: <FileText size={20} />, color: "text-violet-600", bg: "bg-violet-50" },
    { label: "AI Queries",    value: totalQueries,   icon: <MessageSquare size={20} />, color: "text-cyan-600", bg: "bg-cyan-50" },
    { label: "Avg Latency", value: `${avgResponseMs}ms`, icon: <Zap size={20} />, color: "text-amber-600", bg: "bg-amber-50" },
    { label: "System Status", value: isActive ? "Online" : "Idle", icon: <Activity size={20} />, color: "text-emerald-600", bg: "bg-emerald-50" },
  ];

  return (
    <AppShell>
      <div className="p-8 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <header className="mb-10">
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">System Insights</h1>
            <p className="text-gray-500 mt-1">Real-time performance metrics and RAG pipeline health.</p>
          </header>

          {/* KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
            {kpis.map((kpi, i) => (
              <motion.div
                key={kpi.label}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className={`w-12 h-12 ${kpi.bg} ${kpi.color} rounded-2xl flex items-center justify-center mb-4`}>
                  {kpi.icon}
                </div>
                <div className="text-3xl font-bold text-gray-900">{kpi.value}</div>
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-1">{kpi.label}</div>
              </motion.div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            {/* Document Status - Larger Span */}
            <div className="lg:col-span-2 bg-white rounded-3xl shadow-sm border border-gray-100 p-8">
              <div className="flex items-center justify-between mb-8">
                <h2 className="font-bold text-gray-900 flex items-center gap-2">
                  <Database size={18} className="text-primary" />
                  Processing Status
                </h2>
              </div>
              {totalDocs > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={statusData}>
                    <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 12, fontWeight: 500 }} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                    <Tooltip 
                      cursor={{ fill: '#f8fafc' }}
                      contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} 
                    />
                    <Bar dataKey="count" fill={COLORS.primary} radius={[8, 8, 8, 8]} barSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex flex-col items-center justify-center text-gray-400 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                  <p className="text-sm">Awaiting first document upload...</p>
                </div>
              )}
            </div>

            {/* Language Breakdown */}
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8">
              <h2 className="font-bold text-gray-900 flex items-center gap-2 mb-8">
                <Globe2 size={18} className="text-primary" />
                Linguistic Audit
              </h2>
              {pieData.length > 0 ? (
                <div className="flex flex-col items-center">
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        innerRadius={60}
                        outerRadius={80}
                        dataKey="value"
                        paddingAngle={8}
                      >
                        {pieData.map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="none" />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="grid grid-cols-2 gap-4 mt-6 w-full">
                    {pieData.map((item, i) => (
                      <div key={item.name} className="flex items-center gap-2 bg-gray-50 p-3 rounded-2xl">
                        <div className="w-2 h-2 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                        <span className="text-[10px] font-bold text-gray-500 uppercase">{item.name}</span>
                        <span className="ml-auto font-bold text-gray-900">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-gray-400">
                  <p className="text-sm">No linguistic data.</p>
                </div>
              )}
            </div>
          </div>

          {/* Recent Documents Table Style */}
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-8 border-b border-gray-50 flex items-center justify-between">
              <h2 className="font-bold text-gray-900">Recent Ledger Activity</h2>
              <span className="text-xs font-bold text-primary bg-primary/10 px-3 py-1 rounded-full">
                Last {recentDocs.length} entries
              </span>
            </div>
            <div className="overflow-x-auto">
              {recentDocs.length === 0 ? (
                <div className="p-20 text-center text-gray-400">
                   <p>No document activity recorded.</p>
                </div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-gray-50/50">
                      <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-wider text-gray-400">Document</th>
                      <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-wider text-gray-400">Metrics</th>
                      <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-wider text-gray-400">Risks</th>
                      <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-wider text-gray-400">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {recentDocs.map((doc) => (
                      <tr key={doc.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-8 py-5">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-gray-100 rounded-lg text-gray-500">
                              <FileText size={16} />
                            </div>
                            <span className="font-semibold text-gray-800 text-sm truncate max-w-[200px]">
                              {doc.title || doc.filename}
                            </span>
                          </div>
                        </td>
                        <td className="px-8 py-5">
                          <div className="text-xs text-gray-500 flex flex-col gap-1">
                            <span className="flex items-center gap-1 font-medium text-gray-700">
                              <Database size={12} /> {doc.chunk_count} Chunks
                            </span>
                            <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                          </div>
                        </td>
                        <td className="px-8 py-5">
                          {doc.risk_flags && doc.risk_flags.length > 0 ? (
                            <div className="flex items-center gap-1.5 text-rose-600 bg-rose-50 px-2.5 py-1 rounded-lg w-fit">
                              <ShieldAlert size={12} />
                              <span className="text-[10px] font-bold">{doc.risk_flags.length} Flags</span>
                            </div>
                          ) : (
                            <span className="text-[10px] font-bold text-gray-300">No Flags</span>
                          )}
                        </td>
                        <td className="px-8 py-5">
                           <div className="flex items-center gap-2">
                             {doc.status === "ready" && <CheckCircle2 size={14} className="text-emerald-500" />}
                             {doc.status === "processing" && <Clock size={14} className="text-amber-500 animate-pulse" />}
                             {doc.status === "failed" && <AlertCircle size={14} className="text-rose-500" />}
                             <span className="text-xs font-bold text-gray-700 capitalize">{doc.status}</span>
                           </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AppShell>
  );
}