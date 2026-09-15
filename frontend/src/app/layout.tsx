import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hirelens — Career Intelligence",
  description:
    "See your resume the way recruiters and applicant tracking systems do: "
    + "quality scoring, job matching, ATS readiness, and career recommendations.",
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
