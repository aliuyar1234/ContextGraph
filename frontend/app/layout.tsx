import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata = {
  title: "OCG",
  description: "Open Context Graph dashboards"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="shell">
          <header className="site-header reveal">
            <div className="brand-row">
              <p className="eyebrow">Open Context Graph</p>
              <p className="brand-note">privacy-first process intelligence</p>
            </div>
            <nav className="topnav">
              <Link className="chip" href="/">
                Overview
              </Link>
              <Link className="chip" href="/admin">
                Admin
              </Link>
              <Link className="chip" href="/analytics">
                Analytics
              </Link>
              <Link className="chip" href="/personal">
                Personal
              </Link>
            </nav>
          </header>
          {children}
        </main>
      </body>
    </html>
  );
}
