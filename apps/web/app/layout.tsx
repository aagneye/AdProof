import "./globals.css";
import { NavHeader } from "@/components/NavHeader";

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
        <NavHeader />
        {children}
      </body>
    </html>
  );
}
