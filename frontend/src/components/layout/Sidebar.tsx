"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useStore } from "@/store";
import { 
  Menu, 
  X, 
  LayoutDashboard, 
  FileText, 
  MessageSquare, 
  BarChart3, 
  LogOut, 
  Globe,
  Scale
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const NAV = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/documents", icon: FileText, label: "Documents" },
  { href: "/chat", icon: MessageSquare, label: "Ask Wakili" },
  { href: "/analytics", icon: BarChart3, label: "Analytics" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, lang, setLang } = useStore();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  return (
    <>
      <aside
        className={`
          sticky top-0 left-0 z-50
          h-screen bg-white border-r border-gray-100
          transition-all duration-300 ease-in-out
          flex flex-col
          ${collapsed ? "w-20" : "w-64"}
        `}
      >
        {/* Logo Section */}
        <div className="h-16 flex items-center px-6 border-b border-gray-50">
          <div className="flex items-center gap-3">
            <div className="min-w-[32px] h-8 rounded-lg bg-primary flex items-center justify-center text-white shadow-sm">
              <Scale size={18} />
            </div>
            {!collapsed && (
              <motion.span 
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }}
                className="font-display font-bold text-gray-900 text-lg tracking-tight"
              >
                Wakili
              </motion.span>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {NAV.map(({ href, icon: Icon, label }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all group
                  ${active
                    ? "bg-primary/10 text-primary"
                    : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                  }
                  ${collapsed ? "justify-center" : ""}
                `}
                title={collapsed ? label : undefined}
              >
                <Icon size={20} className={active ? "text-primary" : "group-hover:text-gray-900"} />
                {!collapsed && <span>{label}</span>}
                {active && !collapsed && (
                   <motion.div layoutId="activeNav" className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom Actions */}
        <div className="p-4 space-y-2 border-t border-gray-50">
          <button
            onClick={() => setLang(lang === "en" ? "sw" : "en")}
            className={`
              w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider
              text-gray-400 hover:text-primary hover:bg-primary/5 transition-all
              ${collapsed ? "justify-center" : ""}
            `}
          >
            <Globe size={18} />
            {!collapsed && <span>{lang === "en" ? "Kiswahili" : "English"}</span>}
          </button>

          <button
            onClick={handleLogout}
            className={`
              w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider
              text-rose-400 hover:text-rose-600 hover:bg-rose-50 transition-all
              ${collapsed ? "justify-center" : ""}
            `}
          >
            <LogOut size={18} />
            {!collapsed && <span>Sign Out</span>}
          </button>
        </div>

        {/* User Profile */}
        {!collapsed && user && (
          <div className="px-6 py-6 bg-gray-50/50">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-white border border-gray-200 flex items-center justify-center text-primary font-bold shadow-sm">
                {user.full_name?.[0]?.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-gray-900 truncate">{user.full_name}</p>
                <p className="text-[10px] text-gray-500 truncate">{user.email}</p>
              </div>
            </div>
          </div>
        )}

        {/* Collapse Toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-20 w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center text-gray-400 hover:text-primary shadow-sm z-50"
        >
          {collapsed ? <Menu size={12} /> : <X size={12} />}
        </button>
      </aside>
    </>
  );
}