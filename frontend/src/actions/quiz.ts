"use server";

import { api } from "@/lib/api/index.server";
import type { CreateQuizPayload, SubmitQuizAttemptPayload } from "@/types/quiz";

export async function createQuizAction(payload: CreateQuizPayload) {
  return api.quiz.create(payload);
}

export async function submitQuizAttemptAction(
  quizId: number,
  payload: SubmitQuizAttemptPayload,
) {
  return api.quiz.submitAttempt(quizId, payload);
}
