import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXA AI Analyzer",
  description:
    "AI-powered career intelligence: resume analysis, job matching, ATS readiness, and career recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
