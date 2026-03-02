import type { Metadata } from "next";
import Image from "next/image";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PIM AI Coach",
  description:
    "AI-powered coaching assistant for Public Investment Management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-white/95 backdrop-blur-sm">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <a href="/">
                <Image
                  src="/pim-pam-logo.png"
                  alt="PIM PAM"
                  width={120}
                  height={40}
                  priority
                  className="h-auto"
                />
              </a>
              <span className="text-lg font-semibold">AI Coach</span>
            </div>
            <nav className="flex items-center gap-1 text-sm text-[var(--muted-foreground)]">
              <a
                href="/"
                className="rounded-md px-3 py-2 hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
              >
                Home
              </a>
              <a
                href="/coach"
                className="rounded-md px-3 py-2 hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
              >
                Coach
              </a>
              <a
                href="/about"
                className="flex items-center gap-1.5 rounded-md px-3 py-2 hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                About
              </a>
              <a
                href="/release-notes"
                className="flex items-center gap-1.5 rounded-md px-3 py-2 hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
                Release Notes
              </a>
            </nav>
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
