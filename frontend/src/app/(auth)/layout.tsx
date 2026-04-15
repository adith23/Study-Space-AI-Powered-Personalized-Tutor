export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-black">
      <h1 className="text-2xl font-bold text-white mb-8">Study Space</h1>
      {children}
    </div>
  );
}
