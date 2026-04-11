"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/store";

export default function Home() {
  const router = useRouter();
  const token = useStore((s) => s.token);
  useEffect(() => {
    router.replace(token ? "/dashboard" : "/auth/login");
  }, [token, router]);
  return null;
}
