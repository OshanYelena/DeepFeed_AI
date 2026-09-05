import type { Metadata } from "next";
import { Manrope, Literata, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });
const literata = Literata({ subsets: ["latin"], variable: "--font-literata" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "DeepFeed AI — Discover signal. Ignore noise.",
  description: "AI-powered personalized knowledge discovery for engineers and researchers.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${manrope.variable} ${literata.variable} ${jetbrains.variable} font-sans bg-surface text-ink antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
