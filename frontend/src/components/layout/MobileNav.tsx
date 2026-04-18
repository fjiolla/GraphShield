"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/utils/cn";
import {
  LayoutDashboard,
  BarChart3,
  FileText,
  Network,
  Brain,
} from "lucide-react";

const MOBILE_ITEMS = [
  { label: "Home", href: "/", icon: LayoutDashboard },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Audit", href: "/audit", icon: FileText },
  { label: "Graph", href: "/graph-model-audit", icon: Network },
  { label: "Model", href: "/model-audit", icon: Brain },
];

export function MobileNav() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface"
      style={{ boxShadow: "0 -1px 3px rgba(0,0,0,0.06)" }}
    >
      <div className="flex items-center justify-around h-16 px-2">
        {MOBILE_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-0.5 py-1 px-3 rounded-xl",
                "transition-colors duration-150",
                active
                  ? "text-sage-500"
                  : "text-warm-400 hover:text-warm-600"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
