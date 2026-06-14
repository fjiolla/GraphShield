"use client";

import React, { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { MobileNav } from "./MobileNav";
import { AIChatPanel } from "@/components/chat/AIChatPanel";
import { SplashScreen } from "@/components/splash/SplashScreen";
import { cn } from "@/utils/cn";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [showSplash, setShowSplash] = useState(true); // Start true to prevent flash
  const [splashDismissed, setSplashDismissed] = useState(false);

  useEffect(() => {
    const seen = sessionStorage.getItem("graphshield_splash_seen");
    if (seen) {
      setShowSplash(false);
      setSplashDismissed(true);
    }
  }, []);

  const handleEnter = () => {
    setShowSplash(false);
    setSplashDismissed(true);
    sessionStorage.setItem("graphshield_splash_seen", "true");
  };

  return (
    <>
      <AnimatePresence mode="wait">
        {showSplash && <SplashScreen onEnter={handleEnter} />}
      </AnimatePresence>

      {splashDismissed && (
        <div className="flex h-screen overflow-hidden">
          <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
          <div className={cn("flex-1 flex flex-col min-h-0 transition-all duration-300", collapsed ? "md:ml-[72px]" : "md:ml-[256px]")}>
            <TopBar />
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
          <MobileNav />
          <AIChatPanel />
        </div>
      )}
    </>
  );
}
