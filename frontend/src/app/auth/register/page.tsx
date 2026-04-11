"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Scale, Languages, Loader2, User, Mail, Lock } from "lucide-react";
import { useStore } from "@/store";
import { authApi } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const { t, lang, setLang } = useStore();
  const [form, setForm] = useState({ email: "", full_name: "", password: "", preferred_language: "en" });
  const [loading, setLoading] = useState(false);

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.register(form);
      toast.success("Account created successfully!");
      router.push("/auth/login");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  const inputFields = [
    { key: "full_name", label: t("full_name"), type: "text", icon: <User size={18} />, placeholder: "Jane Mwangi" },
    { key: "email", label: t("email"), type: "email", icon: <Mail size={18} />, placeholder: "jane@wakili.legal" },
    { key: "password", label: t("password"), type: "password", icon: <Lock size={18} />, placeholder: "••••••••" },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/5 rounded-full blur-[120px]" />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-[450px] z-10"
      >
        <div className="bg-white rounded-[32px] shadow-xl shadow-gray-200/50 p-10 border border-gray-50">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-4">
              <Scale size={24} />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">{t("register_title")}</h1>
          </div>

          <form onSubmit={handleRegister} className="space-y-5">
            {inputFields.map(({ key, label, type, icon, placeholder }) => (
              <div key={key} className="space-y-1.5">
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-1">{label}</label>
                <div className="relative text-gray-300 focus-within:text-primary transition-colors">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2">{icon}</div>
                  <input
                    type={type}
                    value={(form as any)[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                    required
                    className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 border border-gray-100 rounded-2xl focus:bg-white focus:border-primary focus:ring-4 focus:ring-primary/5 outline-none transition-all text-sm text-gray-900"
                    placeholder={placeholder}
                  />
                </div>
              </div>
            ))}

            <div className="space-y-1.5 pt-2">
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest ml-1">
                {lang === "en" ? "System Language" : "Lugha ya Mfumo"}
              </label>
              <div className="grid grid-cols-2 gap-3">
                {["en", "sw"].map((l) => (
                  <button
                    key={l}
                    type="button"
                    onClick={() => {
                      setForm({ ...form, preferred_language: l });
                      setLang(l as any);
                    }}
                    className={`py-2 rounded-xl border text-[10px] font-bold transition-all ${
                      form.preferred_language === l 
                        ? "border-primary bg-primary text-white shadow-md shadow-primary/20" 
                        : "border-gray-100 bg-gray-50 text-gray-400 hover:border-gray-200"
                    }`}
                  >
                    {l === "en" ? "ENGLISH" : "KISWAHILI"}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 py-4 bg-primary text-white rounded-2xl font-bold text-sm shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all active:scale-[0.98] disabled:opacity-70 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : t("sign_up")}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-50 text-center">
            <p className="text-sm text-gray-400 font-medium">
              {t("have_account")}{" "}
              <Link href="/auth/login" className="text-primary font-bold hover:underline">
                {t("sign_in")}
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}