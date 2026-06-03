import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CRYPTOLENS // SIGNAL ENGINE v1.0",
  description: "AI-driven crypto signal generation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
