import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobFit",
  description: "Close the gap between the CV you have and the role you want.",
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