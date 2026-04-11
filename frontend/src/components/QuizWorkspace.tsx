import { useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";

import type { UploadedFileState } from "./StudySpaceChat";
import {
  createQuiz,
  getQuiz,
  listQuizzes,
  submitQuizAttempt,
} from "../lib/api";
import type {
  QuizAttemptResult,
  QuizDetail,
  QuizDifficulty,
  QuizSummary,
} from "../types/quiz";

interface QuizWorkspaceProps {
  allFiles: UploadedFileState[];
  selectedFileIds: Set<number>;
  onSelectFileForContext: React.Dispatch<React.SetStateAction<Set<number>>>;
}

const difficultyOptions: QuizDifficulty[] = ["easy", "medium", "hard"];
const optionLabels = ["A", "B", "C", "D"];

const QuizWorkspace: React.FC<QuizWorkspaceProps> = ({
  allFiles,
  selectedFileIds,
  onSelectFileForContext,
}) => {
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [activeQuizId, setActiveQuizId] = useState<number | null>(null);
  const [activeQuiz, setActiveQuiz] = useState<QuizDetail | null>(null);
  const [attemptResult, setAttemptResult] = useState<QuizAttemptResult | null>(
    null
  );
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>(
    {}
  );
  const [numberOfQuestions, setNumberOfQuestions] = useState(5);
  const [difficultyLevel, setDifficultyLevel] =
    useState<QuizDifficulty>("medium");
  const [focusPrompt, setFocusPrompt] = useState("");
  const [quizTitle, setQuizTitle] = useState("");
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingQuiz, setIsLoadingQuiz] = useState(false);
  const [isCreatingQuiz, setIsCreatingQuiz] = useState(false);
  const [isSubmittingAttempt, setIsSubmittingAttempt] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const readyFiles = useMemo(
    () => allFiles.filter((file) => file.status === "success"),
    [allFiles]
  );

  useEffect(() => {
    const fetchQuizList = async () => {
      setIsLoadingList(true);
      try {
        const data = await listQuizzes();
        setQuizzes(data);
        if (!activeQuizId && data.length > 0) {
          setActiveQuizId(data[0].id);
        }
      } catch (error) {
        console.error("Failed to fetch quizzes", error);
        setErrorMessage(
          error instanceof Error ? error.message : "Failed to fetch quizzes."
        );
      } finally {
        setIsLoadingList(false);
      }
    };

    fetchQuizList();
  }, []);

  useEffect(() => {
    if (!activeQuizId) {
      setActiveQuiz(null);
      setAttemptResult(null);
      setSelectedAnswers({});
      return;
    }

    let isCancelled = false;
    let pollId: ReturnType<typeof setInterval> | null = null;

    const loadQuiz = async () => {
      setIsLoadingQuiz(true);
      try {
        const data = await getQuiz(activeQuizId);
        if (isCancelled) return;
        setActiveQuiz(data);
        setQuizzes((prev) =>
          prev.map((quiz) => (quiz.id === data.id ? data : quiz))
        );
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
        if (
          (data.status === "pending" || data.status === "generating") &&
          !pollId
        ) {
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
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Failed to fetch quiz detail."
          );
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
  }, [activeQuizId]);

  const handleCreateQuiz = async () => {
    const fileIds = Array.from(selectedFileIds);
    if (fileIds.length === 0) {
      setErrorMessage("Select at least one processed source for quiz generation.");
      return;
    }

    setErrorMessage(null);
    setAttemptResult(null);
    setSelectedAnswers({});
    setIsCreatingQuiz(true);
    try {
      const quiz = await createQuiz({
        file_ids: fileIds,
        number_of_questions: numberOfQuestions,
        difficulty_level: difficultyLevel,
        focus_prompt: focusPrompt.trim() || null,
        title: quizTitle.trim() || null,
      });
      setQuizzes((prev) => [quiz, ...prev.filter((item) => item.id !== quiz.id)]);
      setActiveQuizId(quiz.id);
      setFocusPrompt("");
      setQuizTitle("");
    } catch (error) {
      console.error("Failed to create quiz", error);
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to create quiz."
      );
    } finally {
      setIsCreatingQuiz(false);
    }
  };

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
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to submit quiz attempt."
      );
    } finally {
      setIsSubmittingAttempt(false);
    }
  };

  return (
    <div className="flex h-full gap-4 p-4 overflow-hidden">
      <section className="w-80 shrink-0 rounded-2xl border border-zinc-800 bg-[#222327] p-4 flex flex-col gap-4 overflow-y-auto">
        <div>
          <h2 className="text-lg font-semibold text-white">Create Quiz</h2>
          <p className="text-sm text-zinc-400">
            Broad mode uses all selected source chunks. Add a focus prompt to use semantic retrieval.
          </p>
        </div>

        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-sm text-zinc-300">Sources</label>
            <div className="flex flex-wrap gap-2">
              {readyFiles.length === 0 && (
                <p className="text-sm text-zinc-500">
                  Upload and process documents before creating quizzes.
                </p>
              )}
              {readyFiles.map((file) => (
                <button
                  key={file.id}
                  onClick={() =>
                    onSelectFileForContext((prev) => {
                      const next = new Set(prev);
                      if (next.has(file.id)) {
                        next.delete(file.id);
                      } else {
                        next.add(file.id);
                      }
                      return next;
                    })
                  }
                  className={`rounded-full px-3 py-1 text-xs transition-colors ${
                    selectedFileIds.has(file.id)
                      ? "bg-blue-600 text-white"
                      : "bg-zinc-700 text-zinc-200 hover:bg-zinc-600"
                  }`}
                >
                  {file.name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm text-zinc-300">Title</label>
            <input
              value={quizTitle}
              onChange={(event) => setQuizTitle(event.target.value)}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
              placeholder="Optional quiz title"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm text-zinc-300">
              Number of Questions
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={numberOfQuestions}
              onChange={(event) =>
                setNumberOfQuestions(
                  Math.max(1, Math.min(20, Number(event.target.value) || 1))
                )
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm text-zinc-300">Difficulty</label>
            <select
              value={difficultyLevel}
              onChange={(event) =>
                setDifficultyLevel(event.target.value as QuizDifficulty)
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
            >
              {difficultyOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm text-zinc-300">
              Focus Prompt
            </label>
            <textarea
              value={focusPrompt}
              onChange={(event) => setFocusPrompt(event.target.value)}
              rows={4}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
              placeholder="Optional topic, concept, chapter, or skill to focus the quiz on"
            />
          </div>

          <button
            onClick={handleCreateQuiz}
            disabled={isCreatingQuiz || selectedFileIds.size === 0}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-zinc-700"
          >
            {isCreatingQuiz ? "Creating..." : "Generate Quiz"}
          </button>
        </div>

        <div className="border-t border-zinc-800 pt-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-200">Quizzes</h3>
            {isLoadingList && <Loader2 size={16} className="animate-spin" />}
          </div>
          <div className="space-y-2">
            {quizzes.length === 0 && !isLoadingList && (
              <p className="text-sm text-zinc-500">No quizzes created yet.</p>
            )}
            {quizzes.map((quiz) => (
              <button
                key={quiz.id}
                onClick={() => {
                  setActiveQuizId(quiz.id);
                  setAttemptResult(null);
                  setErrorMessage(null);
                }}
                className={`w-full rounded-xl border px-3 py-3 text-left transition-colors ${
                  activeQuizId === quiz.id
                    ? "border-blue-500 bg-blue-600/15"
                    : "border-zinc-800 bg-zinc-900 hover:border-zinc-700"
                }`}
              >
                <div className="text-sm font-medium text-white">{quiz.title}</div>
                <div className="mt-1 text-xs text-zinc-400">
                  {quiz.status} · {quiz.difficulty_level} · {quiz.number_of_questions} questions
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="flex-1 rounded-2xl border border-zinc-800 bg-[#1f2024] p-6 overflow-y-auto">
        {errorMessage && (
          <div className="mb-4 rounded-xl border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-200">
            {errorMessage}
          </div>
        )}

        {!activeQuizId && (
          <div className="flex h-full items-center justify-center text-zinc-500">
            Select or create a quiz.
          </div>
        )}

        {activeQuizId && isLoadingQuiz && !activeQuiz && (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="animate-spin text-zinc-400" />
          </div>
        )}

        {activeQuiz && (
          <div className="space-y-6">
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
                          const isSelected =
                            selectedAnswers[question.id] === optionLabel;
                          const isCorrectAnswer =
                            result?.correct_option === optionLabel;
                          const isWrongSelected =
                            result?.selected_option === optionLabel &&
                            !result.is_correct;

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
                    className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-zinc-200 disabled:cursor-not-allowed disabled:bg-zinc-600 disabled:text-zinc-300"
                  >
                    {isSubmittingAttempt ? "Submitting..." : "Submit Quiz"}
                  </button>
                )}

                {attemptResult && (
                  <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
                    <h3 className="text-lg font-semibold text-white">
                      Result
                    </h3>
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
      </section>
    </div>
  );
};

export default QuizWorkspace;
