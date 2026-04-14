import { useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";

import type { UploadedFileState } from "@/components/StudySpaceChat";
import {
  createFlashcardDeck,
  getFlashcardDeck,
  listFlashcardDecks,
} from "@/lib/api";
import type {
  CreateFlashcardDeckPayload,
  FlashcardDeckDetail,
  FlashcardDeckSummary,
} from "@/types/flashcard";
import type { QuizDifficulty } from "@/types/quiz";

interface FlashcardWorkspaceProps {
  allFiles: UploadedFileState[];
  selectedFileIds: Set<number>;
  onSelectFileForContext: React.Dispatch<React.SetStateAction<Set<number>>>;
}

const difficultyOptions: QuizDifficulty[] = ["easy", "medium", "hard"];

const FlashcardWorkspace: React.FC<FlashcardWorkspaceProps> = ({
  allFiles,
  selectedFileIds,
  onSelectFileForContext,
}) => {
  const [decks, setDecks] = useState<FlashcardDeckSummary[]>([]);
  const [activeDeckId, setActiveDeckId] = useState<number | null>(null);
  const [activeDeck, setActiveDeck] = useState<FlashcardDeckDetail | null>(null);
  const [revealedCards, setRevealedCards] = useState<Record<number, boolean>>({});
  const [numberOfCards, setNumberOfCards] = useState(10);
  const [difficultyLevel, setDifficultyLevel] =
    useState<QuizDifficulty>("medium");
  const [focusPrompt, setFocusPrompt] = useState("");
  const [deckTitle, setDeckTitle] = useState("");
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingDeck, setIsLoadingDeck] = useState(false);
  const [isCreatingDeck, setIsCreatingDeck] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const readyFiles = useMemo(
    () => allFiles.filter((file) => file.status === "success"),
    [allFiles]
  );

  useEffect(() => {
    const fetchDecks = async () => {
      setIsLoadingList(true);
      try {
        const data = await listFlashcardDecks();
        setDecks(data);
        if (!activeDeckId && data.length > 0) {
          setActiveDeckId(data[0].id);
        }
      } catch (error) {
        console.error("Failed to fetch flashcard decks", error);
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Failed to fetch flashcard decks."
        );
      } finally {
        setIsLoadingList(false);
      }
    };

    fetchDecks();
  }, []);

  useEffect(() => {
    if (!activeDeckId) {
      setActiveDeck(null);
      setRevealedCards({});
      return;
    }

    let isCancelled = false;
    let pollId: ReturnType<typeof setInterval> | null = null;

    const loadDeck = async () => {
      setIsLoadingDeck(true);
      try {
        const data = await getFlashcardDeck(activeDeckId);
        if (isCancelled) return;
        setActiveDeck(data);
        setDecks((prev) =>
          prev.map((deck) => (deck.id === data.id ? data : deck))
        );
        if (
          (data.status === "pending" || data.status === "generating") &&
          !pollId
        ) {
          pollId = setInterval(loadDeck, 3000);
        }
        if (data.status === "ready" || data.status === "failed") {
          if (pollId) {
            clearInterval(pollId);
            pollId = null;
          }
        }
      } catch (error) {
        if (!isCancelled) {
          console.error("Failed to fetch flashcard deck detail", error);
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Failed to fetch flashcard deck detail."
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoadingDeck(false);
        }
      }
    };

    loadDeck();

    return () => {
      isCancelled = true;
      if (pollId) clearInterval(pollId);
    };
  }, [activeDeckId]);

  const handleCreateDeck = async () => {
    const fileIds = Array.from(selectedFileIds);
    if (fileIds.length === 0) {
      setErrorMessage(
        "Select at least one processed source for flashcard generation."
      );
      return;
    }

    setErrorMessage(null);
    setRevealedCards({});
    setIsCreatingDeck(true);
    try {
      const payload: CreateFlashcardDeckPayload = {
        file_ids: fileIds,
        number_of_cards: numberOfCards,
        difficulty_level: difficultyLevel,
        focus_prompt: focusPrompt.trim() || null,
        title: deckTitle.trim() || null,
      };
      const deck = await createFlashcardDeck(payload);
      setDecks((prev) => [deck, ...prev.filter((item) => item.id !== deck.id)]);
      setActiveDeckId(deck.id);
      setFocusPrompt("");
      setDeckTitle("");
    } catch (error) {
      console.error("Failed to create flashcard deck", error);
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to create flashcard deck."
      );
    } finally {
      setIsCreatingDeck(false);
    }
  };

  return (
    <div className="flex h-full gap-4 p-4 overflow-hidden">
      <section className="w-80 shrink-0 rounded-2xl border border-zinc-800 bg-[#222327] p-4 flex flex-col gap-4 overflow-y-auto">
        <div>
          <h2 className="text-lg font-semibold text-white">Create Flashcards</h2>
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
                  Upload and process documents before creating flashcards.
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
              value={deckTitle}
              onChange={(event) => setDeckTitle(event.target.value)}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
              placeholder="Optional deck title"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm text-zinc-300">
              Number of Cards
            </label>
            <input
              type="number"
              min={1}
              max={30}
              value={numberOfCards}
              onChange={(event) =>
                setNumberOfCards(
                  Math.max(1, Math.min(30, Number(event.target.value) || 1))
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
              placeholder="Optional topic, concept, chapter, or skill to focus the deck on"
            />
          </div>

          <button
            onClick={handleCreateDeck}
            disabled={isCreatingDeck || selectedFileIds.size === 0}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-zinc-700"
          >
            {isCreatingDeck ? "Creating..." : "Generate Flashcards"}
          </button>
        </div>

        <div className="border-t border-zinc-800 pt-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-200">Decks</h3>
            {isLoadingList && <Loader2 size={16} className="animate-spin" />}
          </div>
          <div className="space-y-2">
            {decks.length === 0 && !isLoadingList && (
              <p className="text-sm text-zinc-500">No flashcard decks created yet.</p>
            )}
            {decks.map((deck) => (
              <button
                key={deck.id}
                onClick={() => {
                  setActiveDeckId(deck.id);
                  setErrorMessage(null);
                  setRevealedCards({});
                }}
                className={`w-full rounded-xl border px-3 py-3 text-left transition-colors ${
                  activeDeckId === deck.id
                    ? "border-blue-500 bg-blue-600/15"
                    : "border-zinc-800 bg-zinc-900 hover:border-zinc-700"
                }`}
              >
                <div className="text-sm font-medium text-white">{deck.title}</div>
                <div className="mt-1 text-xs text-zinc-400">
                  {deck.status} · {deck.difficulty_level} · {deck.number_of_cards} cards
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

        {!activeDeckId && (
          <div className="flex h-full items-center justify-center text-zinc-500">
            Select or create a flashcard deck.
          </div>
        )}

        {activeDeckId && isLoadingDeck && !activeDeck && (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="animate-spin text-zinc-400" />
          </div>
        )}

        {activeDeck && (
          <div className="space-y-6">
            <header className="border-b border-zinc-800 pb-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-semibold text-white">
                    {activeDeck.title}
                  </h2>
                  <p className="mt-1 text-sm text-zinc-400">
                    {activeDeck.status} · {activeDeck.difficulty_level} · {activeDeck.number_of_cards} cards
                  </p>
                </div>
                {(activeDeck.status === "pending" ||
                  activeDeck.status === "generating") && (
                  <Loader2 className="animate-spin text-zinc-400" />
                )}
              </div>
              {activeDeck.focus_prompt && (
                <p className="mt-3 rounded-lg bg-zinc-900 px-3 py-2 text-sm text-zinc-300">
                  Focus: {activeDeck.focus_prompt}
                </p>
              )}
            </header>

            {activeDeck.status === "failed" && (
              <div className="rounded-xl border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-200">
                {activeDeck.error_message || "Flashcard generation failed."}
              </div>
            )}

            {(activeDeck.status === "pending" ||
              activeDeck.status === "generating") && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-6 text-sm text-zinc-400">
                Flashcard generation is in progress. This view updates automatically.
              </div>
            )}

            {activeDeck.status === "ready" && (
              <>
                <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-400">
                  Sources:{" "}
                  {activeDeck.sources
                    .map((source) => source.name)
                    .filter(Boolean)
                    .join(", ")}
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  {activeDeck.cards.map((card) => {
                    const isRevealed = !!revealedCards[card.id];
                    return (
                      <button
                        key={card.id}
                        onClick={() =>
                          setRevealedCards((prev) => ({
                            ...prev,
                            [card.id]: !prev[card.id],
                          }))
                        }
                        className="min-h-56 rounded-2xl border border-zinc-800 bg-zinc-900 p-5 text-left transition-colors hover:border-zinc-700"
                      >
                        <div className="mb-3 text-xs uppercase tracking-wide text-zinc-500">
                          Card {card.card_order}
                        </div>
                        <div className="text-lg font-medium text-white">
                          {card.front_text}
                        </div>
                        <div className="mt-4 text-sm text-zinc-500">
                          {isRevealed ? "Answer" : "Click to reveal"}
                        </div>
                        {isRevealed && (
                          <div className="mt-4 border-t border-zinc-800 pt-4 text-sm leading-6 text-zinc-300">
                            {card.back_text}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
};

export default FlashcardWorkspace;
