"use client";

import { useEffect, useState } from "react";

interface SnowfallProps {
  enabled: boolean;
}

export function Snowfall({ enabled }: SnowfallProps) {
  const [snowflakes, setSnowflakes] = useState<
    Array<{
      id: number;
      left: number;
      animationDuration: number;
      size: number;
      delay: number;
      windOffset: number;
    }>
  >([]);

  useEffect(() => {
    if (!enabled) {
      setSnowflakes([]);
      return;
    }

    const flakes = Array.from({ length: 100 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      animationDuration: 10 + Math.random() * 15,
      size: 1.5 + Math.random() * 2.5,
      delay: Math.random() * 10,
      windOffset: -20 + Math.random() * 40,
    }));

    setSnowflakes(flakes);
  }, [enabled]);

  if (!enabled) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {snowflakes.map((flake) => (
        <div
          key={flake.id}
          className="absolute animate-fall"
          style={
            {
              left: `${flake.left}%`,
              width: `${flake.size}px`,
              height: `${flake.size}px`,
              animationDuration: `${flake.animationDuration}s`,
              animationDelay: `${flake.delay}s`,
              "--wind-offset": `${flake.windOffset}px`,
            } as React.CSSProperties
          }
        >
          <div className="w-full h-full bg-foreground/60 dark:bg-white/80 rounded-full shadow-lg" />
        </div>
      ))}
      <style jsx>{`
        @keyframes fall {
          0% {
            transform: translateY(-10vh) translateX(0) rotate(0deg);
            opacity: 0;
          }
          10% {
            opacity: 0.7;
          }
          50% {
            transform: translateY(50vh) translateX(var(--wind-offset))
              rotate(180deg);
            opacity: 0.8;
          }
          90% {
            opacity: 0.7;
          }
          100% {
            transform: translateY(110vh)
              translateX(calc(var(--wind-offset) * 1.5)) rotate(360deg);
            opacity: 0;
          }
        }
        .animate-fall {
          animation: fall linear infinite;
        }
      `}</style>
    </div>
  );
}
