"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, X, Send, Bot, User, Loader2 } from "lucide-react";
import { sendChatMessage } from "@/lib/chatApi";
import { useAuditStore } from "@/stores/useAuditStore";
import { useStructStore } from "@/stores/useStructStore";
import { useModelAuditStore } from "@/stores/useModelAuditStore";
import { useGraphModelStore } from "@/stores/useGraphModelStore";
import { cn } from "@/utils/cn";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  provider?: string;
}

const SUGGESTED_QUESTIONS = [
  "Why was this column flagged as sensitive?",
  "Explain disparate impact to a non-technical stakeholder",
  "What regulations require bias auditing?",
  "How can I fix the bias in my hiring model?",
];

export function AIChatPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hi! I'm your AI Fairness Assistant powered by Gemini. Ask me anything about your audit results, fairness metrics, or how to fix detected bias.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [isOpen]);

  const handleSend = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    // Gather current audit context from all stores
    const contextParts: string[] = [];
    const docResult = useAuditStore.getState().result;
    if (docResult) {
      const profile = docResult.findings?.qualitative_analysis?.dynamic_profile;
      contextParts.push(`CURRENT PAGE - Document Audit of "${docResult.filename}": ${JSON.stringify(profile?.summary || {})}. Groups found: ${JSON.stringify(profile?.groups?.map((g: { group_name: string; bias_type: string; bias_intensity: number }) => ({ name: g.group_name, type: g.bias_type, intensity: g.bias_intensity })) || [])}`);
    }
    const structReport = useStructStore.getState().report;
    if (structReport) {
      contextParts.push(`CURRENT PAGE - Dataset Audit: risk=${structReport.risk_level}, bias_detected=${structReport.bias_detected}, summary=${structReport.summary || 'N/A'}`);
    }
    const modelResult = useModelAuditStore.getState().result;
    if (modelResult) {
      contextParts.push(`CURRENT PAGE - Model Audit: verdict=${modelResult.verdict?.bias_verdict}, score=${modelResult.governance?.overall_fairness_score}, worst_group=${modelResult.verdict?.worst_group}, reason=${modelResult.verdict?.verdict_reason}`);
    }
    const graphResult = useGraphModelStore.getState().result;
    if (graphResult) {
      contextParts.push(`CURRENT PAGE - Graph Audit: score=${graphResult.scorecard?.overall_score}, status=${graphResult.scorecard?.overall_status}, findings=${JSON.stringify(graphResult.scorecard?.key_findings || [])}`);
    }

    const auditContext = contextParts.length > 0 ? contextParts.join("\n\n") : undefined;

    try {
      const response = await sendChatMessage(messageText, auditContext);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.reply,
        timestamp: new Date(),
        provider: response.provider,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I couldn't process your request. Please try again in a moment.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-sage-500 text-white shadow-lg hover:bg-sage-600 transition-colors flex items-center justify-center group"
            aria-label="Open AI Assistant"
          >
            <MessageCircle className="w-6 h-6" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-6 right-6 z-50 w-[420px] h-[600px] bg-surface rounded-2xl shadow-modal flex flex-col overflow-hidden border border-warm-200"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-warm-100 bg-sage-50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-sage-500 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-[14px] font-semibold text-warm-800">AI Fairness Assistant</h3>
                  <p className="text-[11px] text-warm-400">Powered by Google Gemini</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 rounded-lg hover:bg-warm-200 flex items-center justify-center transition-colors"
                aria-label="Close chat"
              >
                <X className="w-4 h-4 text-warm-500" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 no-scrollbar">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex gap-2.5",
                    msg.role === "user" ? "flex-row-reverse" : "flex-row"
                  )}
                >
                  <div
                    className={cn(
                      "w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5",
                      msg.role === "user"
                        ? "bg-sage-100 text-sage-600"
                        : "bg-warm-100 text-warm-500"
                    )}
                  >
                    {msg.role === "user" ? (
                      <User className="w-3.5 h-3.5" />
                    ) : (
                      <Bot className="w-3.5 h-3.5" />
                    )}
                  </div>
                  <div
                    className={cn(
                      "max-w-[80%] px-3.5 py-2.5 rounded-2xl text-[13px] leading-relaxed",
                      msg.role === "user"
                        ? "bg-sage-500 text-white rounded-br-md"
                        : "bg-warm-50 text-warm-700 rounded-bl-md border border-warm-100"
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.provider && (
                      <p className="text-[10px] mt-1.5 opacity-60">
                        via {msg.provider === "gemini" ? "Google Gemini" : "Groq"}
                      </p>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-warm-100 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-3.5 h-3.5 text-warm-500" />
                  </div>
                  <div className="bg-warm-50 border border-warm-100 rounded-2xl rounded-bl-md px-4 py-3">
                    <Loader2 className="w-4 h-4 text-sage-500 animate-spin" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Suggested Questions (only show when few messages) */}
            {messages.length <= 2 && !isLoading && (
              <div className="px-4 pb-2">
                <p className="text-[11px] text-warm-400 mb-2">Try asking:</p>
                <div className="flex flex-wrap gap-1.5">
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSend(q)}
                      className="text-[11px] px-2.5 py-1.5 rounded-lg bg-sage-50 text-sage-600 hover:bg-sage-100 transition-colors border border-sage-100"
                    >
                      {q.length > 40 ? q.slice(0, 40) + "..." : q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="px-4 py-3 border-t border-warm-100">
              <div className="flex items-center gap-2 bg-warm-50 rounded-xl px-3 py-2 border border-warm-200 focus-within:border-sage-400 focus-within:ring-2 focus-within:ring-sage-500/20 transition-all">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about bias, fairness, or your audits..."
                  className="flex-1 bg-transparent text-[13px] text-warm-800 placeholder:text-warm-400 focus:outline-none"
                  disabled={isLoading}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim() || isLoading}
                  className="w-8 h-8 rounded-lg bg-sage-500 text-white flex items-center justify-center hover:bg-sage-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  aria-label="Send message"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
