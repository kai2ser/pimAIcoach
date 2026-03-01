import type { Metadata } from "next";
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
        <header className="border-b border-[var(--border)]">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
            <h1 className="text-lg font-semibold">PIM AI Coach</h1>
            <nav className="flex gap-4 text-sm text-[var(--muted-foreground)]">
              <a href="/" className="hover:text-[var(--foreground)]">
                Home
              </a>
              <a href="/coach" className="hover:text-[var(--foreground)]">
                Coach
              </a>
            </nav>
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
