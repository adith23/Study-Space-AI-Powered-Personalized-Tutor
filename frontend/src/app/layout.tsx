import "@/index.css";
import { AuthProvider } from "@/contexts/AuthContext";

export const metadata = {
  title: "Study Space",
  description: "AI-powered personalized tutor",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
