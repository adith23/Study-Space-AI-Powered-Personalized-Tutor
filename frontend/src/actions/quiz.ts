"use server";

import { api } from "@/lib/api/index.server";
import { isNextRedirectError } from "@/lib/api/transport.server";
import type { CreateQuizPayload, SubmitQuizAttemptPayload } from "@/types/quiz";
import type { ActionResult } from "@/types";

export async function createQuizAction(
  spaceId: number,
  payload: CreateQuizPayload,
): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.createQuiz(spaceId, payload);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to create quiz",
      data: null,
    };
  }
}

export async function submitQuizAttemptAction(
  quizId: number,
  payload: SubmitQuizAttemptPayload,
): Promise<ActionResult<any>> {
  try {
    const data = await api.quiz.submitAttempt(quizId, payload);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to submit quiz attempt",
      data: null,
    };
  }
}
