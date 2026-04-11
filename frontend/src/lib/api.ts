import axios from "axios";
import type {
  CreateQuizPayload,
  QuizAttemptResult,
  QuizDetail,
  QuizSummary,
  SubmitQuizAttemptPayload,
} from "../types/quiz";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

function normalizeToken(raw: string | null): string | null {
  if (!raw) return null;
  const token = raw.trim();
  if (!token || token === "undefined" || token === "null") return null;
  return token;
}

// Restore Bearer header before any React effect runs
if (typeof window !== "undefined") {
  const stored = normalizeToken(localStorage.getItem("token"));
  if (stored) {
    api.defaults.headers.common["Authorization"] = `Bearer ${stored}`;
  } else {
    localStorage.removeItem("token");
  }
}

// Attach token dynamically
export function setAuthToken(token: string | null) {
  const normalized = normalizeToken(token);
  if (normalized) {
    api.defaults.headers.common["Authorization"] = `Bearer ${normalized}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
}

export async function createQuiz(payload: CreateQuizPayload) {
  const response = await api.post<QuizSummary>("/materials/quizzes", payload);
  return response.data;
}

export async function listQuizzes() {
  const response = await api.get<QuizSummary[]>("/materials/quizzes");
  return response.data;
}

export async function getQuiz(quizId: number) {
  const response = await api.get<QuizDetail>(`/materials/quizzes/${quizId}`);
  return response.data;
}

export async function submitQuizAttempt(
  quizId: number,
  payload: SubmitQuizAttemptPayload
) {
  const response = await api.post<QuizAttemptResult>(
    `/materials/quizzes/${quizId}/attempts`,
    payload
  );
  return response.data;
}

export async function getQuizAttempt(quizId: number, attemptId: number) {
  const response = await api.get<QuizAttemptResult>(
    `/materials/quizzes/${quizId}/attempts/${attemptId}`
  );
  return response.data;
}

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const message =
        error.response.data?.detail ||
        error.response.data?.message ||
        "An error occurred";
      return Promise.reject(new Error(message));
    } else if (error.request) {
      return Promise.reject(new Error("No response from server"));
    } else {
      return Promise.reject(error);
    }
  }
);

export default api;
