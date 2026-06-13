/**
 * Quiz endpoints — centralized definitions.
 * Every quiz-related API path is defined here ONCE.
 */

import type { Fetcher } from "../types";
import type {
  CreateQuizPayload,
  QuizSummary,
  QuizDetail,
  QuizAttemptResult,
  SubmitQuizAttemptPayload,
} from "@/types/quiz";

export function createQuizApi(fetcher: Fetcher) {
  return {
    /** POST /materials/quizzes — Create a quiz */
    create: (payload: CreateQuizPayload) =>
      fetcher<QuizSummary>("/materials/quizzes", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    /** GET /materials/quizzes — List all quizzes */
    list: () =>
      fetcher<QuizSummary[]>("/materials/quizzes"),

    /** GET /materials/quizzes/{id} — Get quiz detail with questions */
    get: (quizId: number) =>
      fetcher<QuizDetail>(`/materials/quizzes/${quizId}`),

    /** POST /materials/quizzes/{id}/attempts — Submit quiz attempt */
    submitAttempt: (quizId: number, payload: SubmitQuizAttemptPayload) =>
      fetcher<QuizAttemptResult>(
        `/materials/quizzes/${quizId}/attempts`,
        { method: "POST", body: JSON.stringify(payload) },
      ),

    /** GET /materials/quizzes/{id}/attempts/{aid} — Get attempt result */
    getAttempt: (quizId: number, attemptId: number) =>
      fetcher<QuizAttemptResult>(
        `/materials/quizzes/${quizId}/attempts/${attemptId}`,
      ),
  };
}
