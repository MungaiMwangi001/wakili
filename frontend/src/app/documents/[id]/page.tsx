"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";
import { 
  ChevronLeft, 
  MessageSquare, 
  AlertTriangle, 
  ShieldCheck, 
  FileText, 
  Clock,
} from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { useStore } from "@/store";
import { documentsApi } from "@/lib/api";

interface DocumentDetail {
  id: number;
  title: string;
  detected_language: string;
  status: "processing" | "ready";
  clause_summaries?: Array<{ clause_number?: number; title?: string; text?: string; summary?: string }>;
  risk_flags?: Array<{ severity: "high" | "medium" | "low"; type?: string; description?: string; explanation?: string; clause_number?: number }>;
  obligations?: Array<{ obligation: string; party: string; deadline?: string; condition?: string }>;
}

const SEVERITY = {
  high:   { label: "High Risk",   border: "border-rose-500",   bg: "bg-rose-50/50",   pill: "bg-rose-100 text-rose-700", icon: <AlertTriangle size={14} /> },
  medium: { label: "Medium Risk", border: "border-amber-500", bg: "bg-amber-50/50", pill: "bg-amber-100 text-amber-700", icon: <AlertTriangle size={14} /> },
  low:    { label: "Low Risk",    border: "border-emerald-500", bg: "bg-emerald-50/50", pill: "bg-emerald-100 text-emerald-700", icon: <ShieldCheck size={14} /> },
};

export default function DocumentViewerPage() {
  const { id } = useParams();
  const router = useRouter();
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"clauses" | "risks" | "obligations">("clauses");

  // Load and Polling Logic
  useEffect(() => {
    async function load() {
      try {
        const { data } = await documentsApi.get(Number(id));
        setDoc(data);
      } catch {
        toast.error("Document not found");
        router.push("/dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();

    const interval = setInterval(async () => {
      try {
        const { data } = await documentsApi.get(Number(id));
        if (data.status !== "processing") {
          setDoc(data);
          clearInterval(interval);
        }
      } catch { clearInterval(interval); }
    }, 3000);
    return () => clearInterval(interval);
  }, [id, router]);

  if (loading) return (
    <AppShell>
      <div className="flex flex-col items-center justify-center h-[60vh] text-gray-400 gap-4">
        <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
        <p className="text-sm font-semibold animate-pulse">Wakili is analyzing legal frameworks...</p>
      </div>
    </AppShell>
  );

  if (!doc) return null;

  const clauses = doc.clause_summaries || [];
  const risks   = doc.risk_flags || [];
  const obls    = doc.obligations || [];

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-6 py-8">
        
        {/* Breadcrumb & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <div>
            <button
              onClick={() => router.back()}
              className="group flex items-center gap-1 text-xs font-bold text-gray-400 hover:text-primary transition-colors mb-3 uppercase tracking-widest"
            >
              <ChevronLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
              Back to Dashboard
            </button>
            <h1 className="text-2xl md:text-3xl font-display font-bold text-gray-900 leading-tight">
              {doc.title}
            </h1>
            <div className="flex items-center gap-3 mt-2">
              <span className="px-2 py-0.5 rounded bg-gray-100 text-[10px] font-bold text-gray-500 uppercase">
                {doc.detected_language === "sw" ? "Kiswahili" : "English"}
              </span>
              <span className={`text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 ${doc.status === 'ready' ? 'text-emerald-500' : 'text-amber-500'}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${doc.status === 'ready' ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
                {doc.status}
              </span>
            </div>
          </div>

          <button
            onClick={() => router.push(`/chat?doc=${doc.id}`)}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-primary text-white rounded-2xl font-bold text-sm shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all active:scale-[0.98]"
          >
            <MessageSquare size={18} />
            Ask Wakili
          </button>
        </div>

        {/* Tab Navigation (Sticky) */}
        <div className="sticky top-0 z-20 bg-gray-50/80 backdrop-blur-md -mx-6 px-6 py-4 mb-8 border-b border-gray-100">
          <div className="flex p-1 bg-gray-100 rounded-2xl w-full md:w-fit">
            {[
              { id: "clauses", label: "Clauses", icon: <FileText size={16} />, count: clauses.length },
              { id: "risks", label: "Risk Flags", icon: <AlertTriangle size={16} />, count: risks.length },
              { id: "obligations", label: "Obligations", icon: <Clock size={16} />, count: obls.length },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === tab.id 
                    ? "bg-white text-primary shadow-sm" 
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {tab.icon}
                {tab.label}
                {tab.count > 0 && <span className="opacity-50 font-medium">({tab.count})</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4 pb-20"
          >
            {activeTab === "clauses" && (
              clauses.length === 0 ? <EmptyState icon={<FileText />} title="No clauses mapped" /> :
              clauses.map((c: any, i) => (
                <div key={i} className="group bg-white rounded-[24px] p-6 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-[10px] font-black text-primary bg-primary/5 w-6 h-6 rounded flex items-center justify-center">
                      {(c.clause_number ?? i + 1).toString().padStart(2, '0')}
                    </span>
                    <h3 className="font-bold text-gray-900 text-sm">{c.title || `Untitled Section`}</h3>
                  </div>
                  <p className="text-gray-600 text-sm leading-relaxed">{c.text || c.summary}</p>
                </div>
              ))
            )}

            {activeTab === "risks" && (
              risks.length === 0 ? <EmptyState icon={<ShieldCheck />} title="All clear" /> :
              risks.map((r: any, i) => {
                const cfg = SEVERITY[r.severity as keyof typeof SEVERITY] || SEVERITY.medium;
                return (
                  <div key={i} className={`bg-white rounded-[24px] p-6 border-l-4 ${cfg.border} shadow-sm ${cfg.bg}`}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="space-y-1">
                        <span className={`flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest ${cfg.pill} px-2 py-1 rounded-lg w-fit`}>
                          {cfg.icon} {cfg.label}
                        </span>
                        <h4 className="font-bold text-gray-900 pt-1">{r.type || "Undefined Risk"}</h4>
                      </div>
                      {r.clause_number && (
                        <span className="text-[10px] font-bold text-gray-400 bg-white px-2 py-1 rounded-lg border border-gray-100">
                          CLAUSE {r.clause_number}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 text-sm leading-relaxed">{r.description || r.explanation}</p>
                  </div>
                );
              })
            )}

            {activeTab === "obligations" && (
              obls.length === 0 ? <EmptyState icon={<Clock />} title="No pending obligations" /> :
              obls.map((o: any, i: number) => (
                <div key={i} className="bg-white rounded-[24px] p-8 border border-gray-100 shadow-sm">
                  <p className="text-gray-900 font-bold text-base leading-snug mb-6">"{o.obligation}"</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-gray-50">
                    <div>
                      <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Responsible Party</p>
                      <p className="text-sm font-bold text-primary">{o.party}</p>
                    </div>
                    {o.deadline && (
                      <div>
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Deadline / Trigger</p>
                        <p className="text-sm font-bold text-gray-700">{o.deadline}</p>
                      </div>
                    )}
                    {o.condition && (
                      <div className="md:col-span-1">
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Pre-condition</p>
                        <p className="text-xs font-medium text-gray-500 italic">{o.condition}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </AppShell>
  );
}

function EmptyState({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 bg-gray-50/50 rounded-[32px] border-2 border-dashed border-gray-100">
      <div className="text-gray-300 mb-4 scale-[2]">
        {icon}
      </div>
      <p className="text-sm font-bold text-gray-400">{title}</p>
    </div>
  );
}