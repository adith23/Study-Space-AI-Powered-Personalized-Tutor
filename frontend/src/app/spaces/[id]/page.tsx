import { redirect } from "next/navigation";
import { api } from "@/lib/api/index.server";
import StudySpace from "@/components/layout/StudySpace";
import { isNextRedirectError } from "@/lib/api/transport.server";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function SpacePage({ params }: Props) {
  const { id } = await params;
  const spaceId = parseInt(id, 10);

  if (isNaN(spaceId)) {
    redirect("/");
  }

  try {
    // Fetch space details + all scoped data in parallel
    const [space, files, sessions, quizzes, decks, videos] = await Promise.all([
      api.spaces.get(spaceId),
      api.spaces.listFiles(spaceId),
      api.spaces.listChatSessions(spaceId),
      api.spaces.listQuizzes(spaceId),
      api.spaces.listFlashcards(spaceId),
      api.spaces.listVideos(spaceId),
    ]);

    return (
      <StudySpace
        spaceId={spaceId}
        spaceName={space.name}
        initialFiles={files}
        initialSessions={sessions}
        initialQuizzes={quizzes}
        initialDecks={decks}
        initialVideos={videos}
      />
    );
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    redirect("/");
  }
}
