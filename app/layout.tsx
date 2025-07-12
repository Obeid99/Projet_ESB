import Providers from './providers';
import { ReactNode } from "react";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body id="root">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
