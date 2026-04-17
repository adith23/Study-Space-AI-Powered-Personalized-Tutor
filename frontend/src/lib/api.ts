import axios from "axios";
import type {
  CreateFlashcardDeckPayload,
  FlashcardDeckDetail,
  FlashcardDeckSummary,
} from "@/types/flashcard";
import type {
  CreateQuizPayload,
  QuizAttemptResult,
  QuizDetail,
  QuizSummary,
  SubmitQuizAttemptPayload,
} from "@/types/quiz";

// Client-side API requests. They go to the Next.js rewrite proxy.
// Next.js automatically attaches the HttpOnly cookie.
const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

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

export async function createFlashcardDeck(payload: CreateFlashcardDeckPayload) {
  const response = await api.post<FlashcardDeckSummary>(
    "/materials/flashcards",
    payload
  );
  return response.data;
}

export async function listFlashcardDecks() {
  const response = await api.get<FlashcardDeckSummary[]>(
    "/materials/flashcards"
  );
  return response.data;
}

export async function getFlashcardDeck(deckId: number) {
  const response = await api.get<FlashcardDeckDetail>(
    `/materials/flashcards/${deckId}`
  );
  return response.data;
}

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
