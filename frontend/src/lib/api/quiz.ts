import { api } from "./client";
import type {
  CreateQuizPayload,
  QuizAttemptResult,
  QuizDetail,
  QuizSummary,
  SubmitQuizAttemptPayload,
} from "@/types/quiz";

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
