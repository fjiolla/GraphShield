"use client";

import React from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";

export default function ConnectionsPage() {
  return (
    <PageWrapper>
      <PageHeader 
        title="Connections" 
        description="Manage database adapters and LLM API integrations."
      />

      <div className="grid md:grid-cols-2 gap-6">
        <div className="gs-card p-6">
          <div className="flex justify-between items-start mb-4 border-b border-warm-100 pb-2">
             <h3 className="text-[14px] font-semibold text-warm-800">Groq LLM</h3>
             <span className="px-2 py-1 bg-success-50 text-success-600 rounded text-[10px] font-bold uppercase">Connected</span>
          </div>
          <p className="text-[13px] text-warm-600 mb-4">Powers Dynamic Bias Profiling and Narratives via Llama-3-70B.</p>
          <Button variant="outline" size="sm">Configure Key</Button>
        </div>

        <div className="gs-card p-6 opacity-60">
          <div className="flex justify-between items-start mb-4 border-b border-warm-100 pb-2">
             <h3 className="text-[14px] font-semibold text-warm-800">Snowflake Vault</h3>
             <span className="px-2 py-1 bg-warm-100 text-warm-500 rounded text-[10px] font-bold uppercase">Not Configured</span>
          </div>
          <p className="text-[13px] text-warm-600 mb-4">Connect production structured datasets directly.</p>
          <Button variant="outline" size="sm">Add Connection</Button>
        </div>
      </div>
    </PageWrapper>
  );
}
