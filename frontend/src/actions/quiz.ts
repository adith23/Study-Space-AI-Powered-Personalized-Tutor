"use server";

import { api } from "@/lib/api/index.server";
import type { CreateQuizPayload, SubmitQuizAttemptPayload } from "@/types/quiz";

export async function createQuizAction(spaceId: number, payload: CreateQuizPayload) {
  return api.spaces.createQuiz(spaceId, payload);
}

export async function submitQuizAttemptAction(
  quizId: number,
  payload: SubmitQuizAttemptPayload,
) {
  return api.quiz.submitAttempt(quizId, payload);
}
