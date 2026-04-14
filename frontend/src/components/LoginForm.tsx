"use client";

import { useActionState } from "react";
import { loginAction } from "@/actions/auth";

export default function LoginForm() {
  const [state, formAction, isPending] = useActionState(loginAction, undefined);

  return (
    <div className="max-w-sm mx-auto bg-white p-6 rounded-lg shadow-md text-zinc-900">
      <h2 className="text-xl font-semibold mb-4">Login</h2>
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
          name="password"
          type="password"
          placeholder="Password"
          className="w-full mb-4 px-4 py-2 border rounded"
          required
        />
        <button
          type="submit"
          disabled={isPending}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {isPending ? "Logging in..." : "Login"}
        </button>
      </form>
    </div>
  );
}
