import "@/index.css";

export const metadata = {
  title: "Study Space",
  description: "AI-powered personalized tutor",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
