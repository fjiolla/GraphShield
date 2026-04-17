"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/utils/cn";
import {
  LayoutDashboard,
  BarChart3,
  FileText,
  GitFork,
  Network,
  Brain,
  Table2,
  ClipboardList,
  Plug,
  Settings,
  Shield,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  section?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/", icon: LayoutDashboard, section: "Main" },
  { label: "Analytics", href: "/analytics", icon: BarChart3, section: "Main" },
  { label: "Document Audit", href: "/audit", icon: FileText, section: "Audits" },
  { label: "Graph Audit", href: "/graph-audit", icon: GitFork, section: "Audits" },
  { label: "Graph Model Audit", href: "/graph-model-audit", icon: Network, section: "Audits" },
  { label: "Model Audit", href: "/model-audit", icon: Brain, section: "Audits" },
  { label: "Dataset Audit", href: "/struct-audit", icon: Table2, section: "Audits" },
  { label: "Audit Trail", href: "/audit-trail", icon: ClipboardList, section: "System" },
  { label: "Connections", href: "/connections", icon: Plug, section: "System" },
  { label: "Settings", href: "/settings", icon: Settings, section: "System" },
];

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (val: boolean) => void;
}

export function Sidebar({ collapsed, setCollapsed }: SidebarProps) {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  // Group items by section
  const sections = NAV_ITEMS.reduce<Record<string, NavItem[]>>((acc, item) => {
    const section = item.section || "Other";
    if (!acc[section]) acc[section] = [];
    acc[section].push(item);
    return acc;
  }, {});

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col h-screen bg-surface fixed left-0 top-0 z-40",
        "transition-all duration-300 ease-out",
        collapsed ? "w-[72px]" : "w-[256px]"
      )}
      style={{ boxShadow: "1px 0 3px rgba(0,0,0,0.04)" }}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 flex-shrink-0">
        <Link href="/" className="flex items-center gap-2.5 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-sage-500 flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <span className="font-semibold text-[15px] text-warm-800 truncate">
              GraphShield
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto no-scrollbar px-3 py-2 space-y-5">
        {Object.entries(sections).map(([section, items]) => (
          <div key={section}>
            {!collapsed && (
              <p className="px-3 mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-warm-400">
                {section}
              </p>
            )}
            <div className="space-y-0.5">
              {items.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "sidebar-item",
                      active && "sidebar-item-active",
                      collapsed && "justify-center px-0"
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <Icon
                      className={cn(
                        "w-[18px] h-[18px] flex-shrink-0",
                        active ? "text-sage-500" : "text-warm-400"
                      )}
                    />
                    {!collapsed && (
                      <span className="text-[13px] truncate">{item.label}</span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <div className="px-3 py-3 flex-shrink-0">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "sidebar-item w-full",
            collapsed && "justify-center px-0"
          )}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="w-[18px] h-[18px] text-warm-400" />
          ) : (
            <>
              <ChevronLeft className="w-[18px] h-[18px] text-warm-400" />
              <span className="text-[13px]">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
