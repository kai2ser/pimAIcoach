import type { Metadata } from "next";
import Image from "next/image";
import { Inter } from "next/font/google";
import "./globals.css";
import { MobileNav } from "@/components/MobileNav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "PIM AI Coach",
    template: "%s | PIM AI Coach",
  },
  description:
    "AI-powered coaching assistant for Public Investment Management — grounded in international policy documents.",
  metadataBase: new URL("https://pim-a-icoach.vercel.app"),
  openGraph: {
    title: "PIM AI Coach",
    description:
      "AI-powered coaching assistant for Public Investment Management — grounded in international policy documents.",
    url: "https://pim-a-icoach.vercel.app",
    siteName: "PIM AI Coach",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "PIM AI Coach",
    description:
      "AI-powered coaching assistant for Public Investment Management",
  },
  icons: {
    icon: "/pim-pam-logo.png",
    apple: "/pim-pam-logo.png",
  },
  robots: {
    index: true,
    follow: true,
  },
};

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/coach", label: "Coach" },
  { href: "/about", label: "About" },
  { href: "/raging", label: "RAGing" },
  { href: "/statistics", label: "Statistics" },
  { href: "/release-notes", label: "Release Notes" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--background)]/95 backdrop-blur-sm">
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

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-1 text-sm text-[var(--muted-foreground)]">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="rounded-md px-3 py-2 hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </nav>

            {/* Mobile nav */}
            <MobileNav links={NAV_LINKS} />
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
