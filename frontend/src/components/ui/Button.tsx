// src/components/ui/Button.tsx
// Reusable Button with Framer Motion hover/tap animations.

"use client";

import { motion, HTMLMotionProps } from "framer-motion";
import { clsx } from "clsx";

import { ReactNode } from "react";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  children?: React.ReactNode;
}

const variants = {
  primary:   "bg-primary text-white hover:bg-opacity-90 shadow-md",
  secondary: "bg-bg-panel text-primary border border-primary hover:bg-primary hover:text-white",
  danger:    "bg-red-500 text-white hover:bg-red-600",
  ghost:     "text-primary hover:bg-highlight",
};

const sizes = {
  sm: "px-3 py-1.5 text-sm rounded-lg",
  md: "px-5 py-2.5 text-sm rounded-xl",
  lg: "px-7 py-3 text-base rounded-xl2",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.97 }}
      disabled={disabled || loading}
      className={clsx(
        "font-body font-medium transition-all duration-200 inline-flex items-center gap-2",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {loading && (
        <motion.span
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
          className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
        />
      )}
      {children}
    </motion.button>
  );
}
