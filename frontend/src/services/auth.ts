import api from "../lib/api";

interface AuthResponse {
  access_token: string;
  token_type: string;
}

export async function signupUser(data: { username: string; email: string; password: string }): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/auth/signup", data);
  return response.data;
}

export async function loginUser(username: string, password: string): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/auth/login", { username, password });
  return response.data;
}