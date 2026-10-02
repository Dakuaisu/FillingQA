import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";

import "./globals.css";

const geistSans = Geist({ variable: "--font-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FilingQA",
  description: "Citation-grounded answers from SEC 10-K and 10-Q filings, verified claim by claim.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full bg-background text-foreground">
        <header className="border-b">
          <nav className="mx-auto flex max-w-3xl items-center gap-6 px-4 py-3 text-sm">
            <Link href="/" className="font-semibold">
              FilingQA
            </Link>
            <Link href="/" className="text-muted-foreground hover:text-foreground">
              Ask
            </Link>
            <Link href="/corpus" className="text-muted-foreground hover:text-foreground">
              Corpus
            </Link>
            <Link href="/dashboard" className="text-muted-foreground hover:text-foreground">
              Eval dashboard
            </Link>
          </nav>
        </header>
        <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
