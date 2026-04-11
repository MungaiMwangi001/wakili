"use client";
/** AnalyticsCard – stat card for the analytics page. */
import { motion } from "framer-motion";

interface Props {
  title: string;
  value: string | number;
  icon: string;
  color?: string;
  delay?: number;
}

export default function AnalyticsCard({ title, value, icon, color = "bg-analytics", delay = 0 }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className={`${color} rounded-2xl p-6 shadow-card hover:shadow-card-lg transition-shadow`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-display font-bold text-gray-800">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </motion.div>
  );
}
