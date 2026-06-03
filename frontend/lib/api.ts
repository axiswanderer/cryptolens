const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface AnalyzeRequest {
  symbol: string;
  timeframe: "3d" | "7d" | "14d" | "30d";
}

export interface Indicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  ema20: number;
  ema50: number;
  bb_upper: number;
  bb_lower: number;
  bb_mid: number;
  atr: number;
  volume_ratio: number;
  momentum_5d: number;
  momentum_14d: number;
}

export interface AnalyzeResponse {
  symbol: string;
  timeframe: string;
  current_price: number;
  recommendation: "BUY" | "HOLD" | "SELL";
  confidence: number;
  score: number;
  probabilities: { BUY: number; HOLD: number; SELL: number };
  reasons: string[];
  indicators: Indicators;
  timestamp: string;
}

export interface OHLCVPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  analyze: (req: AnalyzeRequest): Promise<AnalyzeResponse> =>
    request("/analyze", { method: "POST", body: JSON.stringify(req) }),

  getOHLCV: (symbol: string, limit = 200): Promise<{ symbol: string; data: OHLCVPoint[]; count: number }> =>
    request(`/ohlcv/${symbol}?limit=${limit}`),

  getSymbols: (): Promise<{ symbols: string[] }> =>
    request("/symbols"),

  getHealth: (): Promise<{ status: string; model_loaded: boolean; db_connected: boolean }> =>
    request("/health"),

  getPredictionHistory: (symbol: string) =>
    request(`/predictions/${symbol}`),
};
