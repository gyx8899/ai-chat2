import type { Metadata } from "next";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Chat",
  description: "智能对话助手",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <ThemeProvider>
          <TooltipProvider delayDuration={0}>
            {children}
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}