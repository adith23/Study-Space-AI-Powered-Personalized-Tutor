"use client";

import { useActionState, useState } from "react";
import Link from "next/link";
import { loginAction } from "@/actions/auth";
import { BookLogo } from "@/components/ui/BookLogo";
import { Eye, EyeOff, Loader2 } from "lucide-react";

export default function LoginForm() {
  const [state, formAction, isPending] = useActionState(loginAction, undefined);
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="w-full max-w-[340px] mx-auto flex flex-col items-center">
      {/* Centered Top Branding */}
      <div className="flex flex-col items-center mb-8">
        <BookLogo className="w-8 h-8 text-white" bookClassName="w-8 h-8" />
        <h2 className="text-3xl font-semibold tracking-tight text-white mt-4 font-sans text-center">
          Sign In
        </h2>
        <p className="text-zinc-400 text-lg mt-3 text-center font-sans">
          Welcome back to Study Space
        </p>
      </div>

      {state?.error && (
        <div className="w-full bg-red-950/40 border border-red-800 text-red-200 text-xs px-4 py-3 rounded-xl mb-4 font-sans text-center">
          {state.error}
        </div>
      )}

      <form action={formAction} className="w-full flex flex-col">
        {/* Username/Email Input */}
        <div className="w-full mb-3.5">
          <input
            className="w-full max-w-[690px] mx-auto bg-transparent text-white border border-zinc-700/80 rounded-full px-5 py-3 text-base placeholder-zinc-500 focus:border-white focus:outline-none transition-all duration-200"
            name="username"
            type="text"
            placeholder="Enter your email or username"
            required
          />
        </div>

        {/* Password Input */}
        <div className="w-full relative">
          <input
            name="password"
            type={showPassword ? "text" : "password"}
            placeholder="Enter your password"
            className="w-full bg-transparent text-white border border-zinc-700/80 rounded-full pl-5 pr-12 py-3 text-base placeholder-zinc-500 focus:border-white focus:outline-none transition-all duration-200"
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white cursor-pointer select-none transition-colors"
          >
            {showPassword ? (
              <EyeOff className="w-4 h-4" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Forgot password link */}
        <div className="w-full flex justify-end mt-1.5">
          <Link
            href="/forgot-password"
            className="text-[13px] text-zinc-400 hover:text-white font-sm transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        {/* Divider */}
        <div className="w-full text-center my-6">
          <span className="text-[13px] text-zinc-500 font-medium tracking-wide">
            or continue with
          </span>
        </div>

        {/* Social Buttons */}
        <div className="w-full flex flex-col gap-2.5">
          <button
            type="button"
            className="w-full flex items-center justify-center bg-[#2c2c2e] hover:bg-[#3a3a3c] text-white py-3 rounded-full font-semibold text-base transition-all duration-200 border border-transparent cursor-pointer active:scale-[0.99]"
          >
            {/* Google Icon */}
            <svg className="w-3.5 h-3.5 mr-2" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            Sign In with Google
          </button>

          <button
            type="button"
            className="w-full flex items-center justify-center bg-[#2c2c2e] hover:bg-[#3a3a3c] text-white py-3 rounded-full font-semibold text-base transition-all duration-200 border border-transparent cursor-pointer active:scale-[0.99]"
          >
            {/* Apple Icon */}
            <svg
              className="w-3.5 h-3.5 fill-current text-white mr-2"
              viewBox="0 0 24 24"
            >
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 4.17c.66-.81 1.11-1.93.99-3.06-1 .04-2.2.67-2.92 1.49-.63.72-1.18 1.86-1.04 2.97 1.12.09 2.24-.57 2.97-1.4" />
            </svg>
            Sign In with Apple
          </button>
        </div>

        {/* Main Sign In Button */}
        <button
          type="submit"
          disabled={isPending}
          className="w-full bg-[#d1d1d6] hover:bg-white text-black py-3 rounded-full font-semibold text-base transition-all duration-200 shadow-md active:scale-[0.99] disabled:opacity-50 mt-8 cursor-pointer flex items-center justify-center gap-2"
        >
          {isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-black" />
              <span>Signing in...</span>
            </>
          ) : (
            "Sign In"
          )}
        </button>
      </form>

      {/* Footer signup link */}
      <div className="mt-6 text-base text-zinc-500 font-sans text-center">
        Don't have an account?{" "}
        <Link
          href="/signup"
          className="text-white font-semibold hover:underline ml-1"
        >
          Sign up
        </Link>
      </div>
    </div>
  );
}
