import type { Metadata } from "next";
import { DM_Sans, Playfair_Display, JetBrains_Mono } from "next/font/google";
import { Toaster } from "react-hot-toast";
import { AppShell } from "@/components/layout/AppShell";
import "./globals.css";

/* ── Font Loading ── */
const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-dm-sans",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["700"],
  variable: "--font-playfair",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-jetbrains",
  display: "swap",
});

/* ── SEO Metadata ── */
export const metadata: Metadata = {
  title: "GraphShield AI — Bias Auditor",
  description:
    "Detect bias, ensure fairness, and build trust. GraphShield audits your documents, AI models, graphs, and datasets with mathematical precision.",
  keywords: [
    "bias detection",
    "fairness audit",
    "AI governance",
    "graph fairness",
    "model audit",
  ],
};

/* ── Root Layout ── */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${dmSans.variable} ${playfair.variable} ${jetbrains.variable}`}
    >
      <body className="antialiased min-h-screen bg-surface-alt text-warm-800">
        <AppShell>{children}</AppShell>
        <Toaster
          position="bottom-right"
          toastOptions={{
            duration: 4000,
            style: {
              fontFamily: "var(--font-dm-sans)",
              fontSize: "14px",
              borderRadius: "12px",
              boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
              padding: "12px 16px",
            },
            success: {
              iconTheme: { primary: "#4D6B44", secondary: "#fff" },
            },
            error: {
              iconTheme: { primary: "#C0392B", secondary: "#fff" },
            },
          }}
        />
      </body>
    </html>
  );
}
