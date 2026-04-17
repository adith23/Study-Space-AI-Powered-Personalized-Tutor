"use client";

import { useActionState } from "react";
import { signupAction } from "@/actions/auth";

export default function SignupForm() {
  const [state, formAction, isPending] = useActionState(signupAction, undefined);

  return (
    <div className="max-w-sm mx-auto bg-white p-6 rounded-lg shadow-md text-zinc-900">
      <h2 className="text-xl font-semibold mb-4">Signup</h2>
      {state?.error && <div className="text-red-600 mb-4">{state.error}</div>}
      <form action={formAction}>
        <input
          name="username"
          type="text"
          placeholder="Username"
          className="w-full mb-3 px-4 py-2 border rounded"
          required
        />
        <input
          name="email"
          type="email"
          placeholder="Email"
          className="w-full mb-3 px-4 py-2 border rounded"
          required
        />
        <input
          name="password"
          type="password"
          placeholder="Password"
          className="w-full mb-4 px-4 py-2 border rounded"
          required
        />
        <button 
          type="submit" 
          disabled={isPending}
          className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          {isPending ? "Creating account..." : "Signup"}
        </button>
      </form>
    </div>
  );
}
