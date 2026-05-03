"use client";

import React, { useEffect, useState } from "react";
import { Loader2, X } from "lucide-react";
import { getQuiz, submitQuizAttempt } from "@/lib/api/quiz";
import type { QuizAttemptResult, QuizDetail } from "@/types/quiz";

interface QuizViewerProps {
  quizId: number;
  onClose: () => void;
}

const optionLabels = ["A", "B", "C", "D"];

const QuizViewer: React.FC<QuizViewerProps> = ({ quizId, onClose }) => {
  const [activeQuiz, setActiveQuiz] = useState<QuizDetail | null>(null);
  const [attemptResult, setAttemptResult] = useState<QuizAttemptResult | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [isLoadingQuiz, setIsLoadingQuiz] = useState(false);
  const [isSubmittingAttempt, setIsSubmittingAttempt] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!quizId) return;

    let isCancelled = false;
    let pollId: ReturnType<typeof setInterval> | null = null;

    const loadQuiz = async () => {
      setIsLoadingQuiz(true);
      try {
        const data = await getQuiz(quizId);
        if (isCancelled) return;
        setActiveQuiz(data);
        
        if (data.status === "ready") {
          setSelectedAnswers((prev) => {
            const next: Record<number, string> = {};
            data.questions.forEach((question) => {
              if (prev[question.id]) {
                next[question.id] = prev[question.id];
              }
            });
            return next;
          });
        }
        
        if ((data.status === "pending" || data.status === "generating") && !pollId) {
          pollId = setInterval(loadQuiz, 3000);
        }
        
        if (data.status === "ready" || data.status === "failed") {
          if (pollId) {
            clearInterval(pollId);
            pollId = null;
          }
        }
      } catch (error) {
        if (!isCancelled) {
          console.error("Failed to fetch quiz detail", error);
          setErrorMessage(error instanceof Error ? error.message : "Failed to fetch quiz detail.");
        }
      } finally {
        if (!isCancelled) {
          setIsLoadingQuiz(false);
        }
      }
    };

    loadQuiz();

    return () => {
      isCancelled = true;
      if (pollId) clearInterval(pollId);
    };
  }, [quizId]);

  const handleSubmitAttempt = async () => {
    if (!activeQuiz || activeQuiz.status !== "ready") return;
    if (activeQuiz.questions.length === 0) return;

    const unanswered = activeQuiz.questions.some(
      (question) => !selectedAnswers[question.id]
    );
    if (unanswered) {
      setErrorMessage("Answer every question before submitting.");
      return;
    }

    setErrorMessage(null);
    setIsSubmittingAttempt(true);
    try {
      const result = await submitQuizAttempt(activeQuiz.id, {
        answers: activeQuiz.questions.map((question) => ({
          question_id: question.id,
          selected_option: selectedAnswers[question.id],
        })),
      });
      setAttemptResult(result);
    } catch (error) {
      console.error("Failed to submit quiz attempt", error);
      setErrorMessage(error instanceof Error ? error.message : "Failed to submit quiz attempt.");
    } finally {
      setIsSubmittingAttempt(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#1e1f22]">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-zinc-800 bg-[#1e1f22] flex-shrink-0">
        <h2 className="text-sm font-semibold text-white">Quiz Viewer</h2>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-zinc-400 truncate max-w-xs" title={activeQuiz?.title || "Loading..."}>
            {activeQuiz?.title || "Loading..."}
          </span>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white transition-colors"
            title="Close viewer"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 p-6 overflow-y-auto">
        {errorMessage && (
          <div className="mb-4 rounded-xl border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-200">
            {errorMessage}
          </div>
        )}

        {isLoadingQuiz && !activeQuiz && (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="animate-spin text-zinc-400" />
          </div>
        )}

        {activeQuiz && (
          <div className="space-y-6 max-w-3xl mx-auto">
            <header className="border-b border-zinc-800 pb-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-semibold text-white">
                    {activeQuiz.title}
                  </h2>
                  <p className="mt-1 text-sm text-zinc-400">
                    {activeQuiz.status} · {activeQuiz.difficulty_level} ·{" "}
                    {activeQuiz.number_of_questions} questions
                  </p>
                </div>
                {(activeQuiz.status === "pending" ||
                  activeQuiz.status === "generating") && (
                  <Loader2 className="animate-spin text-zinc-400" />
                )}
              </div>
              {activeQuiz.focus_prompt && (
                <p className="mt-3 rounded-lg bg-zinc-900 px-3 py-2 text-sm text-zinc-300">
                  Focus: {activeQuiz.focus_prompt}
                </p>
              )}
            </header>

            {activeQuiz.status === "failed" && (
              <div className="rounded-xl border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-200">
                {activeQuiz.error_message || "Quiz generation failed."}
              </div>
            )}

            {(activeQuiz.status === "pending" ||
              activeQuiz.status === "generating") && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-6 text-sm text-zinc-400">
                Quiz generation is in progress. This view updates automatically.
              </div>
            )}

            {activeQuiz.status === "ready" && (
              <>
                <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-400">
                  Sources:{" "}
                  {activeQuiz.sources.map((source) => source.name).filter(Boolean).join(", ")}
                </div>

                <div className="space-y-4">
                  {activeQuiz.questions.map((question) => (
                    <div
                      key={question.id}
                      className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4"
                    >
                      <div className="mb-3 text-sm font-medium text-zinc-200">
                        {question.question_order}. {question.question_text}
                      </div>
                      <div className="space-y-2">
                        {question.options.map((option, index) => {
                          const optionLabel = optionLabels[index];
                          const result = attemptResult?.answers.find(
                            (answer) => answer.question_id === question.id
                          );
                          const isSelected = selectedAnswers[question.id] === optionLabel;
                          const isCorrectAnswer = result?.correct_option === optionLabel;
                          const isWrongSelected = result?.selected_option === optionLabel && !result.is_correct;

                          return (
                            <label
                              key={optionLabel}
                              className={`flex cursor-pointer items-start gap-3 rounded-xl border px-3 py-2 text-sm transition-colors ${
                                isCorrectAnswer
                                  ? "border-green-600 bg-green-900/20"
                                  : isWrongSelected
                                  ? "border-red-600 bg-red-900/20"
                                  : isSelected
                                  ? "border-blue-500 bg-blue-600/10"
                                  : "border-zinc-800 hover:border-zinc-700"
                              }`}
                            >
                              <input
                                type="radio"
                                name={`question-${question.id}`}
                                checked={isSelected}
                                disabled={isSubmittingAttempt || !!attemptResult}
                                onChange={() =>
                                  setSelectedAnswers((prev) => ({
                                    ...prev,
                                    [question.id]: optionLabel,
                                  }))
                                }
                                className="mt-0.5"
                              />
                              <span className="text-zinc-200">
                                {optionLabel}. {option}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>

                {!attemptResult && (
                  <button
                    onClick={handleSubmitAttempt}
                    disabled={isSubmittingAttempt}
                    className="rounded-full bg-blue-600 px-6 py-2.5 text-sm font-bold text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-zinc-700"
                  >
                    {isSubmittingAttempt ? "Submitting..." : "Submit Quiz"}
                  </button>
                )}

                {attemptResult && (
                  <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
                    <h3 className="text-lg font-semibold text-white">Result</h3>
                    <p className="mt-2 text-sm text-zinc-300">
                      Score: {attemptResult.score}/{attemptResult.total_questions}
                    </p>
                    <p className="text-sm text-zinc-400">
                      Percentage: {attemptResult.percentage}%
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default QuizViewer;
