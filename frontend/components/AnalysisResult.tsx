"use client";
import { AnalyzeResponse, OHLCVPoint } from "@/lib/api";
import { Panel, StatBlock, SignalBadge, Bar, ReasonRow, AnimatedNumber } from "@/components/ui";
import { PriceChart } from "@/components/PriceChart";
import { ProbabilityChart } from "@/components/ProbabilityChart";

function fmtPrice(p: number) {
  if (p > 10000) return "$" + Math.round(p).toLocaleString();
  if (p > 1) return "$" + p.toFixed(2);
  return "$" + p.toFixed(4);
}

function getRsiColor(rsi: number): "green" | "amber" | "red" {
  if (rsi < 35) return "green";
  if (rsi > 65) return "red";
  return "amber";
}

export function AnalysisResult({ result, ohlcv }: { result: AnalyzeResponse; ohlcv: OHLCVPoint[] }) {
  const { recommendation, confidence, score, indicators, reasons, current_price, probabilities, symbol, timeframe } = result;
  const sig = recommendation as "BUY" | "HOLD" | "SELL";
  const sigColor = sig === "BUY" ? "var(--green)" : sig === "SELL" ? "var(--red)" : "var(--amber)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

      {/* Main signal */}
      <div className="animate-slide-in s1" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, alignItems: "start" }}>

        {/* Left: signal + bars */}
        <Panel label={`// SIGNAL OUTPUT · ${symbol} · ${timeframe}`} signal={sig}>
          <div style={{ padding: "16px 16px 12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
              <SignalBadge signal={sig} />
              <div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--muted)", marginBottom: 3 }}>
                  CURRENT PRICE
                </div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 24, color: sigColor, textShadow: `0 0 12px ${sigColor}66` }}>
                  {fmtPrice(current_price)}
                </div>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <Bar label="CONFIDENCE" value={confidence} signal={sig} />
              <Bar label="SIGNAL SCORE" value={score} signal={sig} />
            </div>
          </div>
        </Panel>

        {/* Right: probability breakdown */}
        <Panel label="// PROB" signal={sig} style={{ minWidth: 180 }}>
          <div style={{ padding: "12px 14px" }}>
            <ProbabilityChart probabilities={probabilities} />
          </div>
        </Panel>
      </div>

      {/* Chart */}
      <Panel label="// PRICE · 60D" signal={sig} className="animate-slide-in s2">
        <div style={{ padding: "8px 8px 4px" }}>
          <PriceChart data={ohlcv} signal={sig} />
        </div>
      </Panel>

      {/* Indicators grid */}
      <div className="animate-slide-in s3">
        <div style={{
          fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--muted)",
          letterSpacing: "0.15em", marginBottom: 6, paddingLeft: 2
        }}>
          // INDICATOR MATRIX
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
          <StatBlock label="RSI · 14" value={indicators.rsi.toFixed(1)} color={getRsiColor(indicators.rsi)} glow />
          <StatBlock label="MACD" value={(indicators.macd > 0 ? "+" : "") + indicators.macd.toFixed(4)} color={indicators.macd > 0 ? "green" : "red"} />
          <StatBlock label="EMA · 20" value={fmtPrice(indicators.ema20)} color="cyan" />
          <StatBlock label="EMA · 50" value={fmtPrice(indicators.ema50)} color="cyan" />
          <StatBlock label="BB UPPER" value={fmtPrice(indicators.bb_upper)} />
          <StatBlock label="BB LOWER" value={fmtPrice(indicators.bb_lower)} />
          <StatBlock label="VOL RATIO" value={indicators.volume_ratio.toFixed(2) + "×"} color={indicators.volume_ratio > 1.5 ? "green" : "muted"} />
          <StatBlock label="MOM · 5D" value={(indicators.momentum_5d > 0 ? "+" : "") + indicators.momentum_5d.toFixed(1) + "%"} color={indicators.momentum_5d > 0 ? "green" : "red"} />
          <StatBlock label="MOM · 14D" value={(indicators.momentum_14d > 0 ? "+" : "") + indicators.momentum_14d.toFixed(1) + "%"} color={indicators.momentum_14d > 0 ? "green" : "red"} />
        </div>
      </div>

      {/* Reasons */}
      <Panel label="// SIGNAL RATIONALE" signal={sig} className="animate-slide-in s4">
        <div style={{ padding: "4px 14px 10px" }}>
          {reasons.map((r, i) => <ReasonRow key={i} icon="" text={r} />)}
        </div>
      </Panel>

      {/* API footer */}
      <div className="animate-slide-in s5" style={{
        fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--dim)",
        borderTop: "1px solid var(--border)", paddingTop: 8,
        display: "flex", gap: 8, alignItems: "center",
      }}>
        <span style={{ color: "var(--cyan)" }}>POST</span>
        <span>/api/v1/analyze</span>
        <span style={{ color: "var(--muted)" }}>→</span>
        <span>{`{"symbol":"${symbol}","timeframe":"${timeframe}"}`}</span>
      </div>
    </div>
  );
}
