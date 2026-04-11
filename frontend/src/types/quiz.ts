export type QuizDifficulty = "easy" | "medium" | "hard";
export type QuizGenerationMode = "broad_full_source" | "focused_rag";
export type QuizStatus = "pending" | "generating" | "ready" | "failed";

export interface QuizSummary {
  id: number;
  title: string;
  difficulty_level: QuizDifficulty;
  number_of_questions: number;
  focus_prompt: string | null;
  generation_mode: QuizGenerationMode;
  status: QuizStatus;
  error_message: string | null;
}

export interface QuizSource {
  uploaded_file_id: number;
  name: string | null;
}

export interface QuizQuestion {
  id: number;
  question_text: string;
  options: string[];
  question_order: number;
}

export interface QuizDetail extends QuizSummary {
  sources: QuizSource[];
  questions: QuizQuestion[];
}

export interface CreateQuizPayload {
  file_ids: number[];
  number_of_questions: number;
  difficulty_level: QuizDifficulty;
  focus_prompt?: string | null;
  title?: string | null;
}

export interface SubmitQuizAnswerPayload {
  question_id: number;
  selected_option: string;
}

export interface SubmitQuizAttemptPayload {
  answers: SubmitQuizAnswerPayload[];
}

export interface QuizAttemptAnswerResult {
  question_id: number;
  question_text: string;
  options: string[];
  selected_option: string;
  correct_option: string;
  is_correct: boolean;
}

export interface QuizAttemptResult {
  attempt_id: number;
  quiz_id: number;
  score: number;
  percentage: number;
  total_questions: number;
  answers: QuizAttemptAnswerResult[];
}
