"use client";
import { useState, useEffect } from "react";
import { api, AnalyzeResponse, OHLCVPoint } from "@/lib/api";
import { PillGroup, Spinner, Panel } from "@/components/ui";
import { AnalysisResult } from "@/components/AnalysisResult";

const COINS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","ADAUSDT","XRPUSDT","DOTUSDT","AVAXUSDT"];
const TIMEFRAMES = ["3d","7d","14d","30d"] as const;
type TF = typeof TIMEFRAMES[number];

const TICKER_ITEMS = [
  "BTC +2.4%", "ETH -1.1%", "SOL +4.7%", "BNB +0.8%", "ADA -2.3%",
  "XRP +1.2%", "DOT -0.5%", "AVAX +3.1%", "MATIC +2.8%", "LINK +0.3%",
  "BTC.D 54.2%", "TOTAL $2.31T", "FEAR/GREED 68", "DOMINANCE ▲",
];

function Cursor() {
  const [on, setOn] = useState(true);
  useEffect(() => {
    const t = setInterval(() => setOn(p => !p), 530);
    return () => clearInterval(t);
  }, []);
  return <span style={{ opacity: on ? 1 : 0, color: "var(--green)" }}>█</span>;
}

function Clock() {
  const [time, setTime] = useState("");
  useEffect(() => {
    const update = () => setTime(new Date().toISOString().slice(0, 19).replace("T", " ") + " UTC");
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, []);
  return <span>{time}</span>;
}

export default function Home() {
  const [coin, setCoin]         = useState("BTCUSDT");
  const [tf, setTf]             = useState<TF>("7d");
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState<AnalyzeResponse | null>(null);
  const [ohlcv, setOhlcv]       = useState<OHLCVPoint[]>([]);
  const [error, setError]       = useState<string | null>(null);
  const [log, setLog]           = useState<string[]>([]);

  const addLog = (msg: string) => setLog(p => [...p.slice(-4), `> ${msg}`]);

  const handleAnalyze = async () => {
    setLoading(true); setError(null); setResult(null); setLog([]);
    addLog(`INIT ANALYSIS · ${coin} · ${tf}`);
    try {
      addLog("FETCHING OHLCV DATA...");
      const [res, ohlcvRes] = await Promise.all([
        api.analyze({ symbol: coin, timeframe: tf }),
        api.getOHLCV(coin, 200),
      ]);
      addLog("RUNNING XGBOOST PIPELINE...");
      await new Promise(r => setTimeout(r, 300));
      addLog(`SIGNAL COMPUTED · ${res.recommendation} · CONF ${res.confidence}%`);
      setResult(res);
      setOhlcv(ohlcvRes.data);
    } catch (e: any) {
      const msg = e.message || "ANALYSIS FAILED";
      addLog(`ERROR: ${msg}`);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: "relative", zIndex: 1, minHeight: "100vh" }}>

      {/* Moving scan line */}
      <div style={{
        position: "fixed", top: 0, left: 0, right: 0, height: 2,
        background: "linear-gradient(90deg, transparent, rgba(0,255,140,0.15), transparent)",
        animation: "scan-line 6s linear infinite",
        pointerEvents: "none", zIndex: 100,
      }} />

      {/* ── TICKER TAPE ── */}
      <div style={{
        background: "var(--bg2)", borderBottom: "1px solid var(--border)",
        overflow: "hidden", height: 26, display: "flex", alignItems: "center",
      }}>
        <div style={{
          whiteSpace: "nowrap",
          animation: "ticker 40s linear infinite",
          display: "flex", gap: 40,
        }}>
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
            <span key={i} style={{
              fontFamily: "var(--font-mono)", fontSize: 10,
              color: item.includes("+") ? "var(--green)" : item.includes("-") ? "var(--red)" : "var(--muted)",
              letterSpacing: "0.08em",
              textShadow: item.includes("+") ? "0 0 6px var(--green)" : item.includes("-") ? "0 0 6px var(--red)" : "none",
            }}>
              {item}
            </span>
          ))}
        </div>
      </div>

      {/* ── HEADER ── */}
      <header style={{
        borderBottom: "1px solid var(--border)",
        padding: "10px 24px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "var(--bg1)",
      }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <span style={{
            fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700,
            color: "var(--green)", letterSpacing: "0.15em",
            textShadow: "0 0 12px var(--green), 0 0 30px rgba(0,255,140,0.3)",
          }}>
            CRYPTOLENS
          </span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--muted)", letterSpacing: "0.1em" }}>
            // SIGNAL ENGINE v1.0
          </span>
        </div>
        <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{
              width: 6, height: 6, borderRadius: "50%",
              background: "var(--green)", position: "relative",
              boxShadow: "0 0 6px var(--green)",
              animation: "pulse-ring 2s ease-out infinite",
            }} />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--green)" }}>LIVE</span>
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--muted)" }}>
            <Clock />
          </span>
        </div>
      </header>

      {/* ── BODY ── */}
      <div style={{ maxWidth: 860, margin: "0 auto", padding: "20px 16px", display: "flex", flexDirection: "column", gap: 14 }}>

        {/* Input panel */}
        <Panel label="// INPUT CONFIG">
          <div style={{ padding: "14px 16px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--muted)", letterSpacing: "0.15em", marginBottom: 8 }}>
                SELECT ASSET
              </div>
              <PillGroup
                options={COINS.map(c => c.replace("USDT",""))}
                value={coin.replace("USDT","")}
                onChange={v => setCoin(`${v}USDT`)}
              />
            </div>
            <div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--muted)", letterSpacing: "0.15em", marginBottom: 8 }}>
                FORECAST HORIZON
              </div>
              <PillGroup options={[...TIMEFRAMES]} value={tf} onChange={setTf} />
            </div>
          </div>
        </Panel>

        {/* Terminal log */}
        {(log.length > 0 || loading) && (
          <div style={{
            background: "var(--bg1)", border: "1px solid var(--border)",
            padding: "10px 14px", fontFamily: "var(--font-mono)", fontSize: 11,
            color: "var(--green)", lineHeight: 1.8,
          }}>
            {log.map((l, i) => (
              <div key={i} style={{ opacity: i === log.length - 1 ? 1 : 0.45 }}>{l}</div>
            ))}
            {loading && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 2 }}>
                <Spinner />
                <span style={{ color: "var(--muted)" }}>PROCESSING...</span>
                <Cursor />
              </div>
            )}
          </div>
        )}

        {/* Analyze button */}
        <button
          onClick={handleAnalyze}
          disabled={loading}
          style={{
            width: "100%", padding: "12px",
            background: loading ? "var(--bg3)" : "rgba(0,255,140,0.06)",
            border: `1px solid ${loading ? "var(--border)" : "var(--green)"}`,
            color: loading ? "var(--muted)" : "var(--green)",
            fontFamily: "var(--font-display)", fontSize: 13, fontWeight: 600,
            letterSpacing: "0.2em", cursor: loading ? "not-allowed" : "pointer",
            transition: "all 0.15s",
            textShadow: loading ? "none" : "0 0 10px var(--green)",
            boxShadow: loading ? "none" : "inset 0 0 20px rgba(0,255,140,0.03), 0 0 20px rgba(0,255,140,0.05)",
            clipPath: "polygon(8px 0, 100% 0, calc(100% - 8px) 100%, 0 100%)",
          }}
          onMouseEnter={e => {
            if (!loading) (e.target as HTMLElement).style.background = "rgba(0,255,140,0.12)";
          }}
          onMouseLeave={e => {
            if (!loading) (e.target as HTMLElement).style.background = "rgba(0,255,140,0.06)";
          }}
        >
          {loading ? "ANALYZING..." : "▶  EXECUTE ANALYSIS"}
        </button>

        {/* Error */}
        {error && (
          <div style={{
            background: "rgba(255,45,85,0.06)", border: "1px solid rgba(255,45,85,0.3)",
            padding: "10px 14px", fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--red)",
          }}>
            ✕ ERROR: {error}
          </div>
        )}

        {/* Results */}
        {result && ohlcv.length > 0 && (
          <AnalysisResult result={result} ohlcv={ohlcv} />
        )}

        {/* Empty state */}
        {!result && !loading && !error && log.length === 0 && (
          <div style={{
            textAlign: "center", padding: "60px 20px",
            fontFamily: "var(--font-mono)", color: "var(--dim)",
          }}>
            <div style={{ fontSize: 36, marginBottom: 12, color: "var(--border2)" }}>◈</div>
            <div style={{ fontSize: 11, letterSpacing: "0.1em", color: "var(--muted)" }}>
              SELECT ASSET AND EXECUTE ANALYSIS
            </div>
            <div style={{ fontSize: 10, marginTop: 6, color: "var(--dim)" }}>
              AWAITING INPUT <Cursor />
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{
          borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 8,
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--dim)", letterSpacing: "0.1em" }}>
            CRYPTOLENS // NOT FINANCIAL ADVICE // EDUCATIONAL USE ONLY
          </span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--dim)" }}>
            XGB + RULE ENGINE
          </span>
        </div>
      </div>
    </div>
  );
}
