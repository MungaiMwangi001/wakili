"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { 
  FileText, 
  Search, 
  ShieldAlert, 
  Zap, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle,
  FileSearch,
  BookOpen,
  MessageSquare
} from "lucide-react";
import AppShell from "@/components/layout/AppShell";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

export default function DashboardPage() {
  const router = useRouter();

  return (
    <AppShell>
      <div className="min-h-screen bg-gray-50/50 pb-20">
        <div className="max-w-6xl mx-auto px-6 pt-16">
          
          {/* Hero Section */}
          <motion.div 
            initial="hidden"
            animate="visible"
            variants={containerVariants}
            className="text-center mb-20"
          >
            <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              Next-Gen Legal Intelligence
            </motion.div>
            
            <motion.h1 variants={itemVariants} className="font-display text-5xl md:text-6xl font-extrabold text-gray-900 tracking-tight">
              Wakili
            </motion.h1>
            
            <motion.p variants={itemVariants} className="text-xl text-gray-600 mt-6 max-w-2xl mx-auto leading-relaxed">
              Analyze legal documents with <span className="text-primary font-semibold">Retrieval-Augmented Generation (RAG)</span>. 
              Extract insights and detect risks with traceable, source-grounded accuracy.
            </motion.p>
            
            <motion.div variants={itemVariants} className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => router.push("/documents")}
                className="group px-8 py-4 bg-primary text-white rounded-xl font-semibold shadow-lg shadow-primary/25 hover:bg-primary-dark transition-all flex items-center justify-center gap-2"
              >
                Start Analyzing
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </button>
            </motion.div>
          </motion.div>

          {/* Core Logic - RAG Explanation */}
          <motion.section 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="mb-20"
          >
            <div className="bg-white rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100 overflow-hidden">
              <div className="grid md:grid-cols-2">
                <div className="p-8 md:p-12 bg-primary text-white">
                  <h2 className="text-3xl font-bold mb-6 text-white">How Wakili understands your documents</h2>
                  <p className="text-primary-foreground/90 leading-relaxed text-lg">
                    Standard LLMs guess based on general internet data. Wakili uses <strong>RAG</strong> to ground every 
                    answer in your specific file. It acts like a digital paralegal that never misses a detail.
                  </p>
                  <div className="mt-8 space-y-4">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="text-white/60" size={20} />
                      <span>Eliminates AI hallucinations</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="text-white/60" size={20} />
                      <span>Verifiable source citations</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-8 md:p-12 flex flex-col justify-center gap-8">
                  {[
                    { icon: <Search className="text-primary" />, title: "Contextual Search", desc: "Locates exact clauses matching your inquiry." },
                    { icon: <BookOpen className="text-primary" />, title: "Deep Analysis", desc: "LLMs process technical jargon into plain English." },
                    { icon: <FileSearch className="text-primary" />, title: "Traceable Output", desc: "Every response points to the exact page and paragraph." },
                  ].map((step, i) => (
                    <div key={i} className="flex gap-4">
                      <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-primary/5 flex items-center justify-center">
                        {step.icon}
                      </div>
                      <div>
                        <h4 className="font-bold text-gray-900">{step.title}</h4>
                        <p className="text-sm text-gray-500 mt-1">{step.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.section>

          {/* Features Grid */}
          <section className="mb-20">
            <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">Powerful Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { icon: <FileText size={20} />, title: "Multi-Format Parsing", desc: "PDF, DOCX, and TXT up to 20MB automatically indexed." },
                { icon: <ShieldAlert size={20} />, title: "Risk Detection", desc: "Automatically flag high-risk indemnity or liability clauses." },
                { icon: <Zap size={20} />, title: "Instant Summary", desc: "Generate executive summaries for 50+ page contracts in seconds." },
                { icon: <MessageSquare size={20} />, title: "Free-Text Chat", desc: "Ask questions naturally as if speaking to a legal expert." },
                { icon: <CheckCircle2 size={20} />, title: "Kenyan Context", desc: "Optimized for regional legal nuances and Swahili support." },
                { icon: <FileSearch size={20} />, title: "Clause Retrieval", desc: "Pinpoint obligations and deadlines without manual scrolling." },
              ].map((feat, i) => (
                <div key={i} className="p-6 bg-white rounded-2xl border border-gray-100 hover:border-primary/20 hover:shadow-lg transition-all">
                  <div className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center mb-4 text-primary">
                    {feat.icon}
                  </div>
                  <h3 className="font-bold text-gray-900 mb-2">{feat.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{feat.desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Problem/Solution Section */}
          <div className="grid md:grid-cols-2 gap-8 mb-20">
            <div className="bg-white p-8 rounded-3xl border border-red-100 shadow-sm">
              <div className="flex items-center gap-2 mb-6 text-red-600">
                <AlertCircle size={24} />
                <h3 className="font-bold text-xl uppercase tracking-wider">The Problem</h3>
              </div>
              <ul className="space-y-4 text-gray-600">
                <li className="flex gap-3 text-sm">
                  <span className="text-red-400">•</span>
                  Manual review is slow, expensive, and leads to critical human error.
                </li>
                <li className="flex gap-3 text-sm">
                  <span className="text-red-400">•</span>
                  Keyword searches lack semantic context and miss hidden risks.
                </li>
                <li className="flex gap-3 text-sm">
                  <span className="text-red-400">•</span>
                  Small firms lack the budget for high-end legal automation tools.
                </li>
              </ul>
            </div>

            <div className="bg-gray-900 p-8 rounded-3xl shadow-sm text-white">
              <div className="flex items-center gap-2 mb-6 text-primary">
                <CheckCircle2 size={24} />
                <h3 className="font-bold text-xl uppercase tracking-wider">The Solution</h3>
              </div>
              <ul className="space-y-4 text-gray-300">
                <li className="flex gap-3 text-sm">
                  <span className="text-primary">•</span>
                  Uses your document as the <strong>Source of Truth</strong>.
                </li>
                <li className="flex gap-3 text-sm">
                  <span className="text-primary">•</span>
                  Traceable claims with direct links to specific clauses.
                </li>
                <li className="flex gap-3 text-sm">
                  <span className="text-primary">•</span>
                  Cost-effective RAG architecture running on lightweight LLMs.
                </li>
              </ul>
            </div>
          </div>

          {/* CTA Footer */}
          <motion.div 
            whileHover={{ scale: 1.01 }}
            className="relative overflow-hidden bg-primary rounded-3xl p-12 text-center text-white"
          >
            <div className="relative z-10">
              <h2 className="text-3xl font-bold mb-4">Ready to analyze your first document?</h2>
              <p className="text-primary-foreground/80 mb-8 max-w-lg mx-auto">
                Join legal researchers and professionals using Wakili to streamline their workflow.
              </p>
              <button
                onClick={() => router.push("/documents")}
                className="px-10 py-4 bg-white text-primary rounded-xl font-bold shadow-xl hover:bg-gray-50 transition-colors"
              >
                Go to Document Analyzer
              </button>
              <p className="mt-6 text-xs text-primary-foreground/60 italic">
                Wakili is an assistive tool – always consult a qualified lawyer for final decisions.
              </p>
            </div>
            {/* Decorative background circle */}
            <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
          </motion.div>
          
        </div>
      </div>
    </AppShell>
  );
}