"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import { setAuthToken } from "@/lib/api";

interface AuthContextType {
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function normalizeToken(raw: string | null): string | null {
  if (!raw) return null;
  const token = raw.trim();
  if (!token || token === "undefined" || token === "null") return null;
  return token;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);

  // Hydrate token on mount (client-only)
  useEffect(() => {
    const stored = normalizeToken(localStorage.getItem("token"));
    if (!stored) {
      localStorage.removeItem("token");
    }
    setToken(stored);
    // ensure axios + cookie are in sync
    setAuthToken(stored);
  }, []);

  const login = (newToken: string) => {
    const normalized = normalizeToken(newToken);
    if (!normalized) {
      localStorage.removeItem("token");
      setAuthToken(null);
      setToken(null);
      return;
    }
    localStorage.setItem("token", normalized);
    setAuthToken(normalized);
    setToken(normalized);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setAuthToken(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
