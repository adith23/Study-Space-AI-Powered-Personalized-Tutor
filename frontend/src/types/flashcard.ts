import type { QuizDifficulty, QuizGenerationMode, QuizStatus } from "./quiz";

export interface FlashcardDeckSummary {
  id: number;
  title: string;
  difficulty_level: QuizDifficulty;
  number_of_cards: number;
  focus_prompt: string | null;
  generation_mode: QuizGenerationMode;
  status: QuizStatus;
  error_message: string | null;
}

export interface FlashcardDeckSource {
  uploaded_file_id: number;
  name: string | null;
}

export interface FlashcardCard {
  id: number;
  front_text: string;
  back_text: string;
  card_order: number;
}

export interface FlashcardDeckDetail extends FlashcardDeckSummary {
  sources: FlashcardDeckSource[];
  cards: FlashcardCard[];
}

export interface CreateFlashcardDeckPayload {
  file_ids: number[];
  number_of_cards: number;
  difficulty_level: QuizDifficulty;
  focus_prompt?: string | null;
  title?: string | null;
}
