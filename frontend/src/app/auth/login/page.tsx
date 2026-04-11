"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Scale, Mail, Lock, Languages, Loader2 } from "lucide-react";
import { useStore } from "@/store";
import { authApi } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth, t, lang, setLang } = useStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data: tokenData } = await authApi.login(email, password);
      const { data: userData } = await authApi.me(tokenData.access_token);
      setAuth(userData, tokenData.access_token);

      toast.success("Karibu tena / Welcome back!");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Decorative background blur */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-cyan-500/5 rounded-full blur-[120px]" />

      <div className="absolute top-8 right-8">
        <button
          onClick={() => setLang(lang === "en" ? "sw" : "en")}
          className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-white shadow-sm border border-gray-100 text-xs font-bold text-gray-600 hover:border-primary hover:text-primary transition-all"
        >
          <Languages size={14} />
          {lang === "en" ? "KISWAHILI" : "ENGLISH"}
        </button>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-[400px] z-10"
      >
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary text-white shadow-lg shadow-primary/20 mb-6">
            <Scale size={28} />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">{t("login_title")}</h1>
          <p className="text-gray-500 mt-2 text-sm">{t("login_subtitle")}</p>
        </div>

        <div className="bg-white rounded-[32px] shadow-xl shadow-gray-200/50 p-10 border border-gray-50">
          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-1">{t("email")}</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300" size={18} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 border border-gray-100 rounded-2xl focus:bg-white focus:border-primary focus:ring-4 focus:ring-primary/5 outline-none transition-all text-sm"
                  placeholder="wakili@example.com"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-1">{t("password")}</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300" size={18} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 border border-gray-100 rounded-2xl focus:bg-white focus:border-primary focus:ring-4 focus:ring-primary/5 outline-none transition-all text-sm"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-primary text-white rounded-2xl font-bold text-sm shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all active:scale-[0.98] disabled:opacity-70 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : t("sign_in")}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-50 text-center">
            <p className="text-sm text-gray-400 font-medium">
              {t("no_account")}{" "}
              <Link href="/auth/register" className="text-primary font-bold hover:underline">
                {t("sign_up")}
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}