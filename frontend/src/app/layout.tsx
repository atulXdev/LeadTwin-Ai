import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "LeadTwin AI — B2B Lead Intelligence",
  description:
    "AI-powered B2B lead discovery, enrichment, and scoring platform. Find qualified leads automatically.",
  keywords: "B2B leads, lead generation, AI scoring, lead intelligence, SaaS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans antialiased`}
        style={{ background: "#0a0a0f" }}
      >
        {children}
      </body>
    </html>
  );
}
