import Link from "next/link";
import { BookLogo } from "@/components/ui/BookLogo";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-black text-white relative flex flex-col items-center justify-center overflow-x-hidden selection:bg-white/20 selection:text-white">
      {/* Top Left Branding */}
      <div className="absolute top-8 left-8 z-10">
        <Link href="/" className="flex items-center gap-2 group transition-opacity hover:opacity-90">
          <BookLogo className="w-5 h-5 text-white" />
          <span className="font-semibold text-lg tracking-tight text-white font-sans ml-1">
            Study Space
          </span>
        </Link>
      </div>

      {/* Auth Content Container */}
      <main className="w-full max-w-[420px] px-6 py-12 flex flex-col justify-center items-center">
        {children}
      </main>
    </div>
  );
}
