'use client';
import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import { ReactNode } from "react";
import theme from '@/theme/theme';

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <ChakraProvider theme={theme}>{children}</ChakraProvider>
    </>
  );
}
