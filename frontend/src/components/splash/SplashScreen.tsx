"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Lottie from "lottie-react";
import { Shield } from "lucide-react";

interface SplashScreenProps {
  onEnter: () => void;
}

// Floating particles
const PARTICLES = Array.from({ length: 40 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 3 + 1,
  duration: Math.random() * 20 + 15,
  delay: Math.random() * 5,
}));

export function SplashScreen({ onEnter }: SplashScreenProps) {
  const [animationData, setAnimationData] = useState(null);
  const [showButton, setShowButton] = useState(false);
  const [typedText, setTypedText] = useState("");

  const tagline = "Detecting bias. Ensuring fairness. Building trust.";

  useEffect(() => {
    fetch("/splash-animation.json")
      .then((res) => res.json())
      .then((data) => setAnimationData(data))
      .catch(() => onEnter());
  }, [onEnter]);

  useEffect(() => {
    const timer = setTimeout(() => setShowButton(true), 3500);
    return () => clearTimeout(timer);
  }, []);

  // Typing effect
  useEffect(() => {
    let i = 0;
    const startDelay = setTimeout(() => {
      const interval = setInterval(() => {
        if (i < tagline.length) {
          setTypedText(tagline.slice(0, i + 1));
          i++;
        } else {
          clearInterval(interval);
        }
      }, 40);
      return () => clearInterval(interval);
    }, 1200);
    return () => clearTimeout(startDelay);
  }, []);

  if (!animationData) return null;

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center overflow-hidden"
      style={{ background: "linear-gradient(160deg, #0a0a0a 0%, #111318 40%, #0d1117 100%)" }}
      exit={{ opacity: 0, scale: 1.02 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
    >
      {/* Animated particles */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {PARTICLES.map((p) => (
          <motion.div
            key={p.id}
            className="absolute rounded-full"
            style={{
              width: p.size,
              height: p.size,
              left: `${p.x}%`,
              top: `${p.y}%`,
              background: `rgba(77, 107, 68, ${0.2 + Math.random() * 0.3})`,
            }}
            animate={{
              y: [0, -80, 0],
              x: [0, Math.random() * 40 - 20, 0],
              opacity: [0.2, 0.6, 0.2],
            }}
            transition={{
              duration: p.duration,
              repeat: Infinity,
              delay: p.delay,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* Glowing backdrop ring */}
      <motion.div
        className="absolute w-[420px] h-[420px] md:w-[500px] md:h-[500px] rounded-full"
        style={{
          background: "conic-gradient(from 0deg, transparent, rgba(77,107,68,0.12), transparent, rgba(77,107,68,0.08), transparent)",
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
      />

      {/* Inner glow */}
      <div
        className="absolute w-[300px] h-[300px] md:w-[360px] md:h-[360px] rounded-full blur-3xl opacity-20"
        style={{ background: "radial-gradient(circle, #4D6B44, transparent)" }}
      />

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center">
        {/* Lottie with glow border */}
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="relative"
        >
          {/* Pulsing ring behind animation */}
          <motion.div
            className="absolute inset-[-20px] rounded-full border border-[#4D6B44]/30"
            animate={{ scale: [1, 1.05, 1], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute inset-[-40px] rounded-full border border-[#4D6B44]/15"
            animate={{ scale: [1, 1.03, 1], opacity: [0.15, 0.3, 0.15] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
          />
          <div className="w-56 h-56 md:w-72 md:h-72">
            <Lottie animationData={animationData} loop={true} autoplay={true} />
          </div>
        </motion.div>

        {/* Brand */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.7 }}
          className="text-center mt-6"
        >
          <div className="flex items-center justify-center gap-3 mb-3">
            <motion.div
              animate={{ rotateY: [0, 360] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", repeatDelay: 3 }}
            >
              <Shield className="w-8 h-8 text-[#4D6B44]" />
            </motion.div>
            <h1
              className="text-4xl md:text-5xl font-bold tracking-tight"
              style={{
                background: "linear-gradient(135deg, #ffffff 0%, #d4d4d4 50%, #4D6B44 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              GraphShield AI
            </h1>
          </div>

          {/* Typed tagline */}
          <div className="h-6 flex items-center justify-center">
            <p className="text-neutral-400 text-[15px] font-mono">
              {typedText}
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.6, repeat: Infinity }}
                className="text-[#4D6B44]"
              >
                |
              </motion.span>
            </p>
          </div>
        </motion.div>

        {/* Enter Button */}
        <AnimatePresence>
          {showButton && (
            <motion.button
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              onClick={onEnter}
              className="group mt-12 relative px-10 py-3.5 rounded-2xl text-[15px] font-semibold text-white transition-all active:scale-95 overflow-hidden"
              style={{ background: "linear-gradient(135deg, #4D6B44 0%, #3E5637 100%)" }}
            >
              {/* Button shimmer */}
              <motion.div
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)" }}
                animate={{ x: ["-100%", "100%"] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              />
              <span className="relative z-10">Enter Dashboard</span>
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
