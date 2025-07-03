'use client';
import React, { ReactNode, useEffect } from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import theme from '@/theme/theme';
import { useRouter } from 'next/navigation';

export default function RootLayout({ children }: { children: ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const isAuthenticated = localStorage.getItem('authenticated') === 'true';
    if (!isAuthenticated) {
      router.push('/welcome'); // Redirect to the welcome page by default
    }
  }, [router]);

  return (
    <html lang="en">
      <body id="root">
        <ChakraProvider theme={theme}>{children}</ChakraProvider>
      </body>
    </html>
  );
}
