"use client";

import React, { useEffect, useState } from "react";
import { Loader2, X } from "lucide-react";
import { getFlashcardDeck } from "@/lib/api/flashcard";
import type { FlashcardDeckDetail } from "@/types/flashcard";

interface FlashcardViewerProps {
  deckId: number;
  onClose: () => void;
}

const FlashcardViewer: React.FC<FlashcardViewerProps> = ({ deckId, onClose }) => {
  const [activeDeck, setActiveDeck] = useState<FlashcardDeckDetail | null>(null);
  const [revealedCards, setRevealedCards] = useState<Record<number, boolean>>({});
  const [isLoadingDeck, setIsLoadingDeck] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!deckId) return;

    let isCancelled = false;
    let pollId: ReturnType<typeof setInterval> | null = null;

    const loadDeck = async () => {
      setIsLoadingDeck(true);
      try {
        const data = await getFlashcardDeck(deckId);
        if (isCancelled) return;
        setActiveDeck(data);
        
        if ((data.status === "pending" || data.status === "generating") && !pollId) {
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
          setErrorMessage(error instanceof Error ? error.message : "Failed to fetch flashcard deck detail.");
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
  }, [deckId]);

  return (
    <div className="flex flex-col h-full bg-[#1e1f22]">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-zinc-800 bg-[#1e1f22] flex-shrink-0">
        <h2 className="text-sm font-semibold text-white">Flashcards</h2>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-zinc-400 truncate max-w-xs" title={activeDeck?.title || "Loading..."}>
            {activeDeck?.title || "Loading..."}
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

        {isLoadingDeck && !activeDeck && (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="animate-spin text-zinc-400" />
          </div>
        )}

        {activeDeck && (
          <div className="space-y-6 max-w-3xl mx-auto">
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
                        className="min-h-56 rounded-2xl border border-zinc-800 bg-zinc-900 p-5 text-left transition-colors hover:border-zinc-700 hover:bg-zinc-800 focus:outline-none"
                      >
                        <div className="mb-3 text-xs uppercase tracking-wide text-zinc-500">
                          Card {card.card_order}
                        </div>
                        <div className="text-lg font-medium text-white">
                          {card.front_text}
                        </div>
                        <div className="mt-4 text-sm text-blue-400">
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
      </div>
    </div>
  );
};

export default FlashcardViewer;
