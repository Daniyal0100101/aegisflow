import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisFlow | Multi-Agent Operational Decision Support Platform",
  description: "Advanced simulation workspace utilizing parallel specialist agents, validation safety critics, and workflow graph engines.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
