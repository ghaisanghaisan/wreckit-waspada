"use client";

import { motion } from "motion/react";
import { useMemo } from "react";

interface WriteOnTextProps {
  text: string;
  delay?: number;
  duration?: number;
  className?: string;
  staggerChildren?: number;
  onAnimationComplete?: () => void;
}

export function WriteOnText({
  text,
  delay = 0,
  duration = 0.02,
  className = "",
  staggerChildren = 0.02,
  onAnimationComplete,
}: WriteOnTextProps) {
  const characters = useMemo(() => text.split(""), [text]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren,
        delayChildren: delay,
      },
    },
  };

  const characterVariants = {
    hidden: {
      opacity: 0,
    },
    visible: {
      opacity: 1,
    },
  };

  return (
    <motion.div
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      onAnimationComplete={onAnimationComplete}
    >
      {characters.map((char, idx) => (
        <motion.span
          className="inline-block"
          key={idx}
          variants={characterVariants}
        >
          {char === " " ? "\u00A0" : char}
        </motion.span>
      ))}
    </motion.div>
  );
}
