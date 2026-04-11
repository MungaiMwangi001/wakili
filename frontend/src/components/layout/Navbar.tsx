// src/components/layout/Navbar.tsx
// Top navigation bar with language switcher and user menu.

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Scale, LayoutDashboard, FileText, MessageSquare, BarChart3, LogOut, Globe } from "lucide-react";
import { clsx } from "clsx";
import { useStore } from "@/store";
import { useTranslation } from "@/hooks/useTranslation";

const navLinks = [
  { href: "/dashboard",  icon: LayoutDashboard, key: "nav.dashboard" },
  { href: "/documents",  icon: FileText,         key: "nav.documents" },
  { href: "/chat",       icon: MessageSquare,    key: "nav.chat" },
  { href: "/analytics",  icon: BarChart3,        key: "nav.analytics" },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, lang, setLang } = useStore();
  const { t } = useTranslation();

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  const toggleLang = () => setLang(lang === "en" ? "sw" : "en");

  return (
    <nav className="sticky top-0 z-50 glass border-b border-primary/10">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2">
          <Scale size={28} className="text-primary" />
          <span className="font-display text-xl font-bold text-gray-900">Wakili</span>
        </Link>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map(({ href, icon: Icon, key }) => {
            const active = pathname.startsWith(href);
            return (
              <Link key={href} ref={href} href={href}>
                <motion.div
                  whileHover={{ y: -1 }}
                  className={clsx(
                    "flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-colors",
                    active
                      ? "bg-primary text-white shadow-md"
                      : "text-gray-600 hover:text-primary hover:bg-highlight/50"
                  )}
                >
                  <Icon size={16} />
                  {t(key)}
                </motion.div>
              </Link>
            );
          })}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          {/* Language toggle */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleLang}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-primary/20 text-xs font-medium text-primary hover:bg-highlight/50 transition-colors"
          >
            <Globe size={14} />
            {lang === "en" ? "SW" : "EN"}
          </motion.button>

          {/* User avatar + logout */}
          {user && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold">
                {user.full_name[0]}
              </div>
              <button onClick={handleLogout} className="text-gray-400 hover:text-red-500 transition-colors" title={t("nav.logout")}>
                <LogOut size={18} />
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
