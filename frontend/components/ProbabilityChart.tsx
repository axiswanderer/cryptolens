"use client";
import { useEffect, useState } from "react";

const COLORS = { BUY: "#00ff8c", HOLD: "#ffaa00", SELL: "#ff2d55" };

export function ProbabilityChart({ probabilities }: { probabilities: { BUY: number; HOLD: number; SELL: number } }) {
  const [widths, setWidths] = useState({ BUY: 0, HOLD: 0, SELL: 0 });

  useEffect(() => {
    const t = setTimeout(() => setWidths(probabilities), 150);
    return () => clearTimeout(t);
  }, [probabilities]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {(["BUY", "HOLD", "SELL"] as const).map(k => {
        const c = COLORS[k];
        const w = widths[k];
        return (
          <div key={k} style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{
              fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em",
              color: c, minWidth: 38, textShadow: `0 0 6px ${c}`,
            }}>
              {k}
            </span>
            <div style={{ flex: 1, height: 3, background: "var(--bg4)", position: "relative", overflow: "hidden" }}>
              <div style={{
                height: "100%", width: `${w}%`,
                background: `linear-gradient(90deg, ${c}44, ${c})`,
                boxShadow: `0 0 6px ${c}`,
                transition: "width 1s cubic-bezier(0.4,0,0.2,1)",
              }} />
            </div>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: c, minWidth: 40, textAlign: "right" }}>
              {w.toFixed(1)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
