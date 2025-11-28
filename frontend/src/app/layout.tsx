import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import dynamic from 'next/dynamic';

const ClickSpark = dynamic(() => import('@/components/ClickSpark'), { ssr: false });
const CustomCursor = dynamic(() => import('@/components/CustomCursor'), { ssr: false });

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'VALORA - AI Economic Digital Twin',
  description: 'AI-Powered Multi-Agent Economic Digital Twin & Policy Intelligence Platform',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <CustomCursor />
          <ClickSpark
            sparkColor="#60a5fa"
            sparkSize={12}
            sparkRadius={20}
            sparkCount={10}
            duration={500}
          >
            {children}
          </ClickSpark>
        </Providers>
      </body>
    </html>
  );
}
