"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { loginSchema, signupSchema } from "@/lib/schemas/auth";
import type { ActionResult } from "@/types";

const API_BASE_URL =
  process.env.INTERNAL_BACKEND_URL || "http://127.0.0.1:8000/api/v1";

export async function loginAction(
  _prevState: ActionResult<void> | undefined,
  formData: FormData,
): Promise<ActionResult<void>> {
  const username = formData.get("username") as string;
  const password = formData.get("password") as string;

  // Zod Client-Side Form Validation
  const validation = loginSchema.safeParse({ username, password });
  if (!validation.success) {
    const errorMsg = validation.error.errors.map((e) => e.message).join(", ");
    return { error: errorMsg, data: null };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(validation.data),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      return { error: data.detail || "Failed to login", data: null };
    }

    if (!data.access_token || !data.refresh_token) {
      return { error: "Invalid response from server.", data: null };
    }

    // Secure HttpOnly Cookie
    const cookieStore = await cookies();
    cookieStore.set("access_token", data.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60, // 1 hour
      path: "/",
    });

    cookieStore.set("refresh_token", data.refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: "/",
    });
  } catch (error) {
    console.error("Login action error:", error);
    return { error: "An unexpected error occurred.", data: null };
  }

  // Redirect after success (must be outside try/catch in most cases)
  redirect("/");
}

export async function signupAction(
  _prevState: ActionResult<void> | undefined,
  formData: FormData,
): Promise<ActionResult<void>> {
  const username = formData.get("username") as string;
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  // Zod Client-Side Form Validation
  const validation = signupSchema.safeParse({ username, email, password });
  if (!validation.success) {
    const errorMsg = validation.error.errors.map((e) => e.message).join(", ");
    return { error: errorMsg, data: null };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(validation.data),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      return { error: data.detail || "Failed to sign up", data: null };
    }

    if (!data.access_token || !data.refresh_token) {
      return { error: "Invalid response from server.", data: null };
    }

    const cookieStore = await cookies();
    cookieStore.set("access_token", data.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60,
      path: "/",
    });

    cookieStore.set("refresh_token", data.refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7,
      path: "/",
    });
  } catch (error) {
    console.error("Signup action error:", error);
    return { error: "An unexpected error occurred.", data: null };
  }

  redirect("/");
}

export async function logoutAction(): Promise<ActionResult<void>> {
  const cookieStore = await cookies();
  cookieStore.delete("access_token");
  cookieStore.delete("refresh_token");
  redirect("/login");
}
