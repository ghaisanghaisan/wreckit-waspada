"use client";

import { motion, useInView } from "motion/react";
import { ReactNode, useRef } from "react";

interface AnimateOnViewProps {
  children: ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
  animation?:
    | "fadeUp"
    | "fadeIn"
    | "slideInLeft"
    | "slideInRight"
    | "scaleIn"
    | "rotateIn";
  once?: boolean;
  margin?: any;
}

const animationVariants = {
  fadeUp: {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  },
  fadeIn: {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  },
  slideInLeft: {
    hidden: { opacity: 0, x: -50 },
    visible: { opacity: 1, x: 0 },
  },
  slideInRight: {
    hidden: { opacity: 0, x: 50 },
    visible: { opacity: 1, x: 0 },
  },
  scaleIn: {
    hidden: { opacity: 0, scale: 0.8 },
    visible: { opacity: 1, scale: 1 },
  },
  rotateIn: {
    hidden: { opacity: 0, rotate: -10 },
    visible: { opacity: 1, rotate: 0 },
  },
};

export function AnimateOnView({
  children,
  delay = 0,
  duration = 0.5,
  className = "",
  animation = "fadeUp",
  once = true,
  margin = "-100px",
}: AnimateOnViewProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once, margin });
  const variants = animationVariants[animation];

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      variants={variants}
      transition={{ duration, delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
