import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ClerkProvider } from '@clerk/nextjs';
import '../src/index.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Dienstwünsche - DRK Köln',
  description: 'Dienstwunsch-Formular für Mitarbeiter',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="de">
        <body className={inter.className}>{children}</body>
      </html>
    </ClerkProvider>
  );
}
