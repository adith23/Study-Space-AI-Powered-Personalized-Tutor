import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

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
  const [token, setToken] = useState<string | null>(() => {
    const normalized = normalizeToken(localStorage.getItem("token"));
    if (!normalized) {
      localStorage.removeItem("token");
      return null;
    }
    return normalized;
  });

  const login = (newToken: string) => {
    const normalized = normalizeToken(newToken);
    if (!normalized) {
      localStorage.removeItem("token");
      setToken(null);
      return;
    }
    localStorage.setItem("token", normalized);
    setToken(normalized);
  };

  const logout = () => {
    localStorage.removeItem("token");
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
