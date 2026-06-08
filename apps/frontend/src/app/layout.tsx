import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "DeepFeed AI — Discover signal. Ignore noise.",
  description: "AI-powered personalized knowledge discovery for engineers and researchers.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrains.variable} font-sans bg-surface text-slate-100 antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
