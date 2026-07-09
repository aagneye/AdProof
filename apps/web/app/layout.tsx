import "./globals.css";
import { NavHeader } from "@/components/NavHeader";
import { Providers } from "@/components/Providers";

export const metadata = {
  title: "AdProof",
  description: "AI ads with cryptographic provenance",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <NavHeader />
          {children}
        </Providers>
      </body>
    </html>
  );
}
