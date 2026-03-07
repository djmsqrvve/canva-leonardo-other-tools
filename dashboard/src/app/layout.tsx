import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Twilight Shadowpunk Asset Pipeline",
  description: "Automated asset generation for DJ MSQRVVE",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-cyan-500/30">
        {children}
      </body>
    </html>
  );
}
