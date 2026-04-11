"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/store";
import Sidebar from "./Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const token = useStore((s) => s.token);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    if (!token) {
      router.replace("/auth/login");
    }
  }, [token, router]);

  // Prevent hydration mismatch and ensure auth check happens before render
  if (!isMounted || !token) return null;

  return (
    <div className="flex min-h-screen bg-white">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden bg-gray-50/30">
        {children}
      </main>
    </div>
  );
}