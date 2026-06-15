import { NextRequest } from "next/server";
import { serverTransportRaw } from "@/lib/api/transport.server";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ videoId: string }> },
) {
  const { videoId } = await params;
  const res = await serverTransportRaw(`/videos/${videoId}/thumbnail`);

  if (!res.ok) {
    return new Response("Thumbnail not found", { status: res.status });
  }

  return new Response(res.body, {
    headers: {
      "Content-Type": res.headers.get("content-type") || "image/jpeg",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
