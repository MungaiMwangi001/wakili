"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Upload, 
  Trash2, 
  FileText, 
  AlertCircle, 
  ShieldAlert,
  CheckCircle, 
  Clock, 
  Plus, 
  Languages, 
  Calendar,
  MessageSquare,
  Search,
  ChevronRight
} from "lucide-react";
import toast from "react-hot-toast";
import AppShell from "@/components/layout/AppShell";
import { useStore } from "@/store";
import { documentsApi } from "@/lib/api";

interface Doc {
  id: number;
  title: string;
  filename: string;
  file_type: string;
  status: "processing" | "ready" | "failed";
  detected_language: string | null;
  created_at: string;
  risk_flags?: any[];
}

const STATUS_CONFIG = {
  ready:      { icon: CheckCircle, color: "text-emerald-500",  bg: "bg-emerald-50",  label: "Analyzed"    },
  processing: { icon: Clock,       color: "text-amber-500",    bg: "bg-amber-50",    label: "Processing"  },
  failed:     { icon: AlertCircle, color: "text-rose-500",     bg: "bg-rose-50",     label: "Failed"      },
};

export default function DocumentsPage() {
  const router = useRouter();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocs();
  }, []);

  async function loadDocs() {
    try {
      const { data } = await documentsApi.list();
      setDocs(data);
    } catch {
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(file: File) {
    if (!file) return;
    const allowed = ["pdf", "docx", "txt", "png", "jpg", "jpeg"];
    const ext = file.name.split(".").pop()?.toLowerCase();

    if (!allowed.includes(ext || "")) {
      toast.error(`Unsupported file type. Use: ${allowed.join(", ")}`);
      return;
    }
    
    setUploading(true);
    try {
      const { data } = await documentsApi.upload(file);
      setDocs((prev) => [data, ...prev]);
      setShowUpload(false);
      toast.success("Document added to pipeline.");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(docId: number, title: string) {
    if (!confirm(`Permanently delete "${title}"?`)) return;
    setDeleting(docId);
    try {
      await documentsApi.delete(docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
      toast.success("Document removed.");
    } catch (err: any) {
      toast.error("Delete failed.");
    } finally {
      setDeleting(null);
    }
  }

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-6 py-10">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Your Library</h1>
            <p className="text-gray-500 mt-1">Manage and audit your legal repository with RAG intelligence.</p>
          </div>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="inline-flex items-center gap-2 px-5 py-3 bg-primary text-white rounded-xl text-sm font-semibold shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            {showUpload ? <Plus className="rotate-45 transition-transform" /> : <Upload size={18} />}
            {showUpload ? "Close" : "New Document"}
          </button>
        </div>

        {/* Improved Upload Dropzone */}
        <AnimatePresence>
          {showUpload && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-10"
            >
              <div
                onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files[0]); }}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onClick={() => fileRef.current?.click()}
                className={`relative group border-2 border-dashed rounded-3xl p-12 text-center transition-all duration-300
                  ${dragOver ? "border-primary bg-primary/5 scale-[1.01]" : "border-gray-200 bg-white hover:border-primary/40 hover:bg-gray-50/50"}`}
              >
                <input ref={fileRef} type="file" className="hidden" onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} />
                
                {uploading ? (
                  <div className="flex flex-col items-center gap-4">
                    <div className="relative">
                      <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                    </div>
                    <p className="text-primary font-medium">Processing through RAG Pipeline...</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center text-gray-400 group-hover:text-primary group-hover:bg-primary/10 transition-colors mb-4">
                      <Upload size={32} />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900">Push to Analyzer</h3>
                    <p className="text-gray-500 text-sm mt-1 max-w-xs mx-auto">
                      Drop your legal file here. We support PDF, DOCX, and TXT up to 20MB.
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* List Content */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-gray-100 rounded-2xl animate-pulse border border-gray-200" />
            ))}
          </div>
        ) : docs.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-32 bg-white rounded-3xl border border-gray-100 shadow-sm">
            <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <FileText className="text-gray-300" size={40} />
            </div>
            <h3 className="text-xl font-bold text-gray-900">No documents found</h3>
            <p className="text-gray-500 mt-2">Your analyzed legal files will appear here.</p>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AnimatePresence mode="popLayout">
              {docs.map((doc) => {
                const cfg = STATUS_CONFIG[doc.status] ?? STATUS_CONFIG.processing;
                const highRisks = (doc.risk_flags || []).filter((r: any) => r.severity === "high").length;

                return (
                  <motion.div
                    key={doc.id}
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="group relative bg-white rounded-2xl p-5 border border-gray-100 hover:border-primary/20 hover:shadow-xl hover:shadow-gray-200/40 transition-all"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gray-50 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-colors shrink-0">
                        <FileText size={24} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-md ${cfg.bg} ${cfg.color}`}>
                            {cfg.label}
                          </span>
                          <span className="text-[10px] text-gray-400 flex items-center gap-1">
                            <Calendar size={12} />
                            {new Date(doc.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        
                        <h3 className="font-bold text-gray-900 truncate pr-6 group-hover:text-primary transition-colors cursor-pointer" 
                            onClick={() => doc.status === "ready" && router.push(`/documents/${doc.id}`)}>
                          {doc.title || doc.filename}
                        </h3>

                        <div className="flex items-center gap-4 mt-3">
                          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                            {doc.detected_language === "sw" ? "Kiswahili" : "English"}
                          </div>
                          {highRisks > 0 && (
                            <div className="flex items-center gap-1 text-xs text-rose-600 font-semibold bg-rose-50 px-2 py-0.5 rounded-full">
                              <ShieldAlert size={14} />
                              {highRisks} Risks
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 pt-4 border-t border-gray-50 flex items-center justify-between">
                      <button 
                        onClick={() => router.push(`/chat?doc=${doc.id}`)}
                        disabled={doc.status !== "ready"}
                        className="flex items-center gap-2 text-sm font-bold text-primary hover:text-primary-dark disabled:opacity-30 transition-colors"
                      >
                        <MessageSquare size={16} />
                        Consult LLM
                      </button>
                      
                      <div className="flex items-center gap-2">
                         <button
                           onClick={() => handleDelete(doc.id, doc.title || doc.filename)}
                           className="p-2 text-gray-300 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-all"
                         >
                           <Trash2 size={16} />
                         </button>
                         <ChevronRight size={18} className="text-gray-300 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </div>
    </AppShell>
  );
}