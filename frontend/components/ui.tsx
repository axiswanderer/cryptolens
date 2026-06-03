"use client";
import { clsx } from "clsx";
import { ReactNode, useEffect, useRef, useState } from "react";

// ── Terminal Panel ────────────────────────────────────────────────────────

export function Panel({
  children,
  className,
  label,
  signal,
  flicker = false,
}: {
  children: ReactNode;
  className?: string;
  label?: string;
  signal?: "BUY" | "HOLD" | "SELL";
  flicker?: boolean;
}) {
  const accent = signal === "BUY" ? "var(--green)" : signal === "SELL" ? "var(--red)" : signal === "HOLD" ? "var(--amber)" : "var(--green)";

  return (
    <div
      className={clsx("relative", flicker && "animate-[flicker_8s_ease-in-out_infinite]", className)}
      style={{
        background: "var(--bg2)",
        border: `1px solid ${accent}33`,
        clipPath: "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%)",
      }}
    >
      {/* Corner accent */}
      <div style={{
        position: "absolute", top: 0, right: 0, width: 12, height: 12,
        borderBottom: `1px solid ${accent}66`, borderLeft: `1px solid ${accent}66`,
        background: "var(--bg)",
      }} />
      {/* Top scan bar */}
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${accent}88, transparent)` }} />
      {label && (
        <div style={{ padding: "4px 12px", borderBottom: `1px solid ${accent}22`, background: `${accent}06` }}>
          <span style={{ color: accent, fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.15em", textShadow: `0 0 8px ${accent}` }}>
            {label}
          </span>
        </div>
      )}
      <div>{children}</div>
    </div>
  );
}

// ── Stat Block ────────────────────────────────────────────────────────────

export function StatBlock({
  label,
  value,
  sub,
  color = "green",
  glow = false,
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: "green" | "red" | "amber" | "cyan" | "muted";
  glow?: boolean;
}) {
  const colorMap = {
    green: "var(--green)",
    red:   "var(--red)",
    amber: "var(--amber)",
    cyan:  "var(--cyan)",
    muted: "var(--muted)",
  };
  const c = colorMap[color];

  return (
    <div style={{
      background: "var(--bg3)",
      border: "1px solid var(--border)",
      padding: "10px 12px",
      clipPath: "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)",
    }}>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--muted)", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{
        fontFamily: "var(--font-mono)", fontSize: 18, color: c, fontWeight: 400,
        textShadow: glow ? `0 0 8px ${c}, 0 0 20px ${c}66` : undefined,
      }}>
        {value}
      </div>
      {sub && <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--muted)", marginTop: 3 }}>{sub}</div>}
    </div>
  );
}

// ── Signal Badge ──────────────────────────────────────────────────────────

export function SignalBadge({ signal }: { signal: "BUY" | "HOLD" | "SELL" }) {
  const cfg = {
    BUY:  { color: "var(--green)", bg: "rgba(0,255,140,0.08)",  border: "rgba(0,255,140,0.4)" },
    HOLD: { color: "var(--amber)", bg: "rgba(255,170,0,0.08)",  border: "rgba(255,170,0,0.4)" },
    SELL: { color: "var(--red)",   bg: "rgba(255,45,85,0.08)",  border: "rgba(255,45,85,0.4)" },
  }[signal];

  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 8,
      border: `1px solid ${cfg.border}`, background: cfg.bg,
      padding: "8px 20px",
      clipPath: "polygon(6px 0, 100% 0, calc(100% - 6px) 100%, 0 100%)",
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: "50%", background: cfg.color,
        boxShadow: `0 0 8px ${cfg.color}, 0 0 16px ${cfg.color}`,
        animation: "pulse-ring 1.5s ease-out infinite",
      }} />
      <span style={{
        fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 700,
        color: cfg.color, letterSpacing: "0.25em",
        textShadow: `0 0 12px ${cfg.color}, 0 0 30px ${cfg.color}66`,
      }}>
        {signal}
      </span>
    </div>
  );
}

// ── Bar ───────────────────────────────────────────────────────────────────

export function Bar({
  label, value, signal, showPct = true,
}: {
  label: string; value: number; signal: "BUY" | "HOLD" | "SELL"; showPct?: boolean;
}) {
  const [width, setWidth] = useState(0);
  useEffect(() => { const t = setTimeout(() => setWidth(value), 100); return () => clearTimeout(t); }, [value]);

  const color = signal === "BUY" ? "var(--green)" : signal === "SELL" ? "var(--red)" : "var(--amber)";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--muted)", letterSpacing: "0.08em", minWidth: 88 }}>
        {label}
      </span>
      <div style={{ flex: 1, height: 4, background: "var(--bg4)", position: "relative", overflow: "visible" }}>
        <div style={{
          height: "100%", width: `${width}%`,
          background: `linear-gradient(90deg, ${color}88, ${color})`,
          boxShadow: `0 0 8px ${color}`,
          transition: "width 1s cubic-bezier(0.4, 0, 0.2, 1)",
        }} />
        {/* Tick marks */}
        {[25,50,75].map(t => (
          <div key={t} style={{
            position: "absolute", top: -2, left: `${t}%`, width: 1, height: 8,
            background: "var(--dim)", transform: "translateX(-50%)",
          }} />
        ))}
      </div>
      {showPct && (
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color, minWidth: 36, textAlign: "right", textShadow: `0 0 6px ${color}` }}>
          {value}%
        </span>
      )}
    </div>
  );
}

// ── Pill Selector ─────────────────────────────────────────────────────────

export function PillGroup<T extends string>({
  options, value, onChange,
}: {
  options: T[]; value: T; onChange: (v: T) => void;
}) {
  return (
    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
      {options.map(opt => {
        const active = opt === value;
        return (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            style={{
              padding: "5px 14px",
              border: active ? "1px solid var(--green)" : "1px solid var(--border)",
              background: active ? "rgba(0,255,140,0.1)" : "var(--bg3)",
              color: active ? "var(--green)" : "var(--muted)",
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              letterSpacing: "0.1em",
              cursor: "pointer",
              transition: "all 0.12s",
              clipPath: "polygon(4px 0, 100% 0, calc(100% - 4px) 100%, 0 100%)",
              textShadow: active ? "0 0 8px var(--green)" : "none",
            }}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

// ── Spinner ───────────────────────────────────────────────────────────────

export function Spinner() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{
        width: 14, height: 14,
        border: "1px solid var(--border)",
        borderTop: "1px solid var(--green)",
        borderRadius: "50%",
        animation: "spin 0.6s linear infinite",
      }} />
    </div>
  );
}

// ── Reason Row ────────────────────────────────────────────────────────────

export function ReasonRow({ icon, text }: { icon: string; text: string }) {
  const isPos = text.includes("oversold") || text.includes("Bullish") || text.includes("uptrend") || text.includes("cheap") || text.includes("positive") || text.includes("surge") || text.includes("+");
  const isNeg = text.includes("overbought") || text.includes("Bearish") || text.includes("downtrend") || text.includes("extended") || text.includes("fading");
  const color = isPos ? "var(--green)" : isNeg ? "var(--red)" : "var(--amber)";
  const arrow = isPos ? "▲" : isNeg ? "▼" : "◆";

  return (
    <div style={{
      display: "flex", gap: 10, padding: "9px 0",
      borderBottom: "1px solid var(--border)", alignItems: "flex-start",
    }}>
      <span style={{ color, fontFamily: "var(--font-mono)", fontSize: 10, marginTop: 2, flexShrink: 0 }}>{arrow}</span>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text)", lineHeight: 1.5 }}>{text}</span>
    </div>
  );
}

// ── Animated Number ───────────────────────────────────────────────────────

export function AnimatedNumber({ value, prefix = "", suffix = "", decimals = 2 }: {
  value: number; prefix?: string; suffix?: string; decimals?: number;
}) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<number>(0);

  useEffect(() => {
    const start = ref.current;
    const end = value;
    const duration = 800;
    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (end - start) * eased;
      setDisplay(current);
      ref.current = current;
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [value]);

  return (
    <span>{prefix}{display.toFixed(decimals)}{suffix}</span>
  );
}
