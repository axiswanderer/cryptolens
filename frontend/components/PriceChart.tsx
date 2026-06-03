"use client";
import { useEffect, useRef } from "react";
import { OHLCVPoint } from "@/lib/api";

const COLORS = { BUY: "#00ff8c", HOLD: "#ffaa00", SELL: "#ff2d55" };

export function PriceChart({ data, signal }: { data: OHLCVPoint[]; signal: "BUY" | "HOLD" | "SELL" }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;

    const load = async () => {
      const { createChart, ColorType, CrosshairMode } = await import("lightweight-charts");
      if (chartRef.current) { chartRef.current.remove(); chartRef.current = null; }

      const color = COLORS[signal];
      const chart = createChart(containerRef.current!, {
        layout: {
          background: { type: ColorType.Solid, color: "transparent" },
          textColor: "#4a7a5e",
          fontSize: 10,
          fontFamily: "'Share Tech Mono', monospace",
        },
        grid: {
          vertLines: { color: "rgba(0,255,140,0.04)" },
          horzLines: { color: "rgba(0,255,140,0.04)" },
        },
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: { color: `${color}66`, width: 1, style: 3 },
          horzLine: { color: `${color}66`, width: 1, style: 3 },
        },
        rightPriceScale: { borderColor: "rgba(0,255,140,0.12)" },
        timeScale: { borderColor: "rgba(0,255,140,0.12)", timeVisible: false },
        width: containerRef.current!.clientWidth,
        height: 200,
      });
      chartRef.current = chart;

      const area = chart.addAreaSeries({
        lineColor: color,
        topColor: `${color}22`,
        bottomColor: `${color}00`,
        lineWidth: 1,
        crosshairMarkerRadius: 3,
        crosshairMarkerBorderColor: color,
        crosshairMarkerBackgroundColor: "#020304",
      });

      area.setData(
        data.map(d => ({
          time: Math.floor(new Date(d.timestamp).getTime() / 1000) as any,
          value: d.close,
        }))
      );
      chart.timeScale().fitContent();

      const resize = () => containerRef.current && chart.applyOptions({ width: containerRef.current.clientWidth });
      window.addEventListener("resize", resize);
      return () => window.removeEventListener("resize", resize);
    };

    load();
    return () => { if (chartRef.current) { chartRef.current.remove(); chartRef.current = null; } };
  }, [data, signal]);

  return <div ref={containerRef} style={{ width: "100%", height: 200 }} />;
}
