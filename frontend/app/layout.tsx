import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Trendart.AI Curator UI",
  description:
    "Run the Global Curator Scout memo generator from a web UI built with Next.js.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
