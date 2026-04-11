"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, 
  ChevronDown, 
  Trash2, 
  Info, 
  Scale, 
  AlertTriangle,
  History,
  FileText,
  Clock,
  ShieldCheck
} from "lucide-react";
import toast from "react-hot-toast";
import AppShell from "@/components/layout/AppShell";
import { ChatBubble, RiskBadge } from "@/components/ui/index";
import { useStore } from "@/store";
import { documentsApi, askApi } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  language?: string;
  risk_flags?: any[];
  obligations?: any[];
  retrieved_chunks?: any[];
}

interface HistoryEntry {
  role: "user" | "assistant";
  content: string;
}

const SAMPLE_QUESTIONS = {
  en: [
    "What are my termination rights?",
    "Are there any unlimited liability clauses?",
    "Summarise the payment obligations.",
    "What are the notice periods?",
  ],
  sw: [
    "Haki zangu za kusimamisha mkataba ni zipi?",
    "Je, kuna vifungu vya dhima isiyo na mipaka?",
    "Fanya muhtasari wa wajibu wa malipo.",
    "Vipindi vya arifa ni vipi?",
  ],
};

function ChatContent() {
  const searchParams = useSearchParams();
  const { lang } = useStore();
  const [docs, setDocs] = useState<any[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    documentsApi.list().then((r) => {
      const ready = r.data.filter((d: any) => d.status === "ready");
      setDocs(ready);
      const docId = searchParams.get("doc");
      if (docId) setSelectedDoc(docId);
    }).catch(() => {});
  }, [searchParams]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const sendMessage = async (text?: string) => {
    const q = (text || input).trim();
    if (!q) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setThinking(true);
    
    try {
      const { data } = await askApi.ask(
        q,
        selectedDoc ? Number(selectedDoc) : undefined,
        lang,
        history
      );

      const assistantMessage: Message = {
        role: "assistant",
        content: typeof data.answer === 'object' ? JSON.stringify(data.answer) : data.answer,
        language: data.language,
        risk_flags: data.risk_flags,
        obligations: data.obligations,
        retrieved_chunks: data.retrieved_chunks,
      };

      setMessages((m) => [...m, assistantMessage]);
      setHistory((prev) => [
        ...prev,
        { role: "user", content: q },
        { role: "assistant", content: typeof data.answer === 'string' ? data.answer : "Structured Analysis Provided" },
      ]);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Something went wrong");
    } finally {
      setThinking(false);
    }
  };

  const clearConversation = () => {
    if (confirm("Clear current conversation history?")) {
      setMessages([]);
      setHistory([]);
    }
  };

  const renderAssistantContent = (msg: Message) => {
    try {
      const data = JSON.parse(msg.content);
      return (
        <div className="space-y-4">
          <p className="text-sm leading-relaxed font-body text-gray-800">
            {data.answer}
          </p>

          {msg.obligations && msg.obligations.length > 0 && (
            <div className="bg-primary/5 rounded-2xl p-4 border border-primary/10">
              <div className="flex items-center gap-2 mb-3">
                <Clock size={14} className="text-primary" />
                <span className="text-[10px] font-black uppercase tracking-widest text-primary">Actionable Obligations</span>
              </div>
              <div className="space-y-3">
                {msg.obligations.map((ob, idx) => (
                  <div key={idx} className="flex flex-col border-b border-primary/5 pb-2 last:border-0 last:pb-0">
                    <span className="text-xs font-bold text-gray-700">{ob.obligation}</span>
                    <div className="flex justify-between items-center mt-1">
                       <span className="text-[10px] text-gray-500 italic">{ob.condition}</span>
                       <span className="text-[10px] font-bold text-primary px-2 py-0.5 bg-white rounded border border-primary/10">{ob.party}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    } catch (e) {
      return <p className="text-sm font-body text-gray-800">{msg.content}</p>;
    }
  };

  const questions = SAMPLE_QUESTIONS[lang as keyof typeof SAMPLE_QUESTIONS] || SAMPLE_QUESTIONS.en;

  return (
    <AppShell>
      <div className="flex flex-col h-screen max-h-screen bg-gray-50/30">
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 px-8 py-4 border-b border-gray-100 bg-white/80 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white shadow-lg">
              <Scale size={20} />
            </div>
            <div>
              <h1 className="text-xl font-display font-bold text-gray-900 tracking-tight">Wakili Intelligence</h1>
              <p className="text-[10px] uppercase tracking-widest font-black text-primary flex items-center gap-1">
                 RAG-Driven Audit Mode
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative group">
              <select
                value={selectedDoc}
                onChange={(e) => setSelectedDoc(e.target.value)}
                className="appearance-none bg-white border border-gray-200 rounded-xl px-4 py-2.5 pr-10 text-xs font-bold focus:ring-2 focus:ring-primary/20 outline-none transition-all cursor-pointer shadow-sm min-w-[200px]"
              >
                <option value="">Full Repository Search</option>
                {docs.map((d) => (
                  <option key={d.id} value={d.id}>{d.title || d.filename}</option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-3.5 text-gray-400 pointer-events-none" />
            </div>

            {messages.length > 0 && (
              <button
                onClick={clearConversation}
                className="p-2.5 text-gray-400 hover:text-rose-500 hover:bg-rose-50 border border-gray-100 rounded-xl transition-all"
              >
                <Trash2 size={18} />
              </button>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 md:px-20 py-8 space-y-8">
          {messages.length === 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto mt-12 text-center">
              <div className="w-16 h-16 bg-primary/5 rounded-2xl flex items-center justify-center mx-auto mb-6 text-primary">
                <ShieldCheck size={32} />
              </div>
              <h2 className="text-3xl font-display font-bold text-gray-900">Consult with Wakili</h2>
              <p className="text-gray-500 font-body mt-2 mb-8">Select a document to begin a deep-dive legal analysis.</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {questions.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="text-left text-xs bg-white border border-gray-100 rounded-2xl p-4 text-gray-700 hover:border-primary/40 hover:bg-primary/5 transition-all shadow-sm flex items-center gap-3 group"
                  >
                    <div className="w-6 h-6 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-primary/10">
                      <Info size={12} className="text-gray-400 group-hover:text-primary" />
                    </div>
                    {q}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <AnimatePresence mode="popLayout">
            {messages.map((msg, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
              >
                {/* Fixed User Bubble: Solid Primary Background with Bold White Text */}
                <div className={`max-w-[85%] p-6 rounded-3xl ${
                  msg.role === "user" 
                  ? "bg-primary text-white shadow-lg shadow-primary/20 rounded-tr-none border border-primary-dark/10" 
                  : "bg-white border border-gray-100 shadow-card rounded-tl-none"
                }`}>
                  {msg.role === "assistant" ? (
                    renderAssistantContent(msg)
                  ) : (
                    <p className="text-sm font-bold leading-relaxed opacity-100">
                      {msg.content}
                    </p>
                  )}
                </div>
                
                {msg.role === "assistant" && (
                  <div className="mt-4 ml-4 w-full max-w-2xl space-y-4">
                    {msg.retrieved_chunks && msg.retrieved_chunks.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {msg.retrieved_chunks.map((chunk, idx) => (
                          <div key={idx} className="flex items-center gap-1.5 px-2 py-1 bg-white border border-gray-200 rounded-lg text-[10px] font-bold text-gray-500 shadow-sm transition-hover hover:border-primary/40">
                            <FileText size={10} className="text-primary" />
                            {chunk.document_title || "Source"} {chunk.clause_number && `· §${chunk.clause_number}`}
                          </div>
                        ))}
                      </div>
                    )}

                    {msg.risk_flags && msg.risk_flags.length > 0 && (
                      <div className="grid grid-cols-1 gap-2">
                        {msg.risk_flags.map((r, j) => (
                          <motion.div 
                            key={j}
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="bg-rose-50/50 border border-rose-100 rounded-xl p-3 flex items-start gap-3"
                          >
                            <AlertTriangle size={14} className="text-rose-500 mt-1 shrink-0" />
                            <div>
                               <div className="flex items-center gap-2 mb-1">
                                 <p className="font-black text-[10px] text-rose-900 uppercase tracking-tight">{r.risk_type?.replace(/_/g, " ")}</p>
                                 <RiskBadge severity={r.severity} />
                               </div>
                               <p className="text-xs text-rose-800 font-body leading-snug">{r.explanation}</p>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {thinking && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 ml-4 py-4">
              <div className="flex gap-1.5">
                {[0, 0.1, 0.2].map((d) => (
                  <motion.div
                    key={d}
                    className="w-1.5 h-1.5 rounded-full bg-primary"
                    animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 0.8, delay: d, repeat: Infinity }}
                  />
                ))}
              </div>
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400">Analyzing Jurisprudence...</span>
            </motion.div>
          )}
          <div ref={bottomRef} className="h-4" />
        </div>

        <div className="max-w-4xl w-full mx-auto px-4 pb-10 pt-2">
          <div className="relative flex items-center bg-white rounded-[2rem] shadow-card-lg border border-gray-100 p-2 focus-within:ring-2 focus-within:ring-primary/10 transition-all">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Ask Wakili about your contract..."
              className="flex-1 text-sm bg-transparent px-5 py-3 outline-none font-body placeholder:text-gray-300"
              disabled={thinking}
            />
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => sendMessage()}
              disabled={!input.trim() || thinking}
              className="w-12 h-12 rounded-2xl bg-primary text-white flex items-center justify-center disabled:opacity-20 shadow-lg shadow-primary/30 transition-all hover:bg-primary-dark ml-2 shrink-0"
            >
              <Send size={18} />
            </motion.button>
          </div>
          <p className="text-[10px] text-center text-gray-400 mt-4 font-medium uppercase tracking-widest">
            RAG-generated analysis. Verify with a legal professional.
          </p>
        </div>
      </div>
    </AppShell>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center font-display text-primary animate-pulse">Initializing Wakili...</div>}>
      <ChatContent />
    </Suspense>
  );
}