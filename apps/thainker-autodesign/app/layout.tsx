import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'The ThAInker Autodesign',
  description: '由 Codex 驱动的贡献导向实验设计与执行工作台。',
  openGraph: {
    title: 'The ThAInker Autodesign',
    description: '从 idea.md 到可审计的实验证据。',
    images: [{
      url: 'https://thainker-autodesign.jscz7ckyn7.chatgpt.site/og.png',
      width: 1732,
      height: 909,
      alt: 'The ThAInker Autodesign',
    }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'The ThAInker Autodesign',
    description: '从 idea.md 到可审计的实验证据。',
    images: ['https://thainker-autodesign.jscz7ckyn7.chatgpt.site/og.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
