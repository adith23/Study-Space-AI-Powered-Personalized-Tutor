import { NextRequest } from "next/server";
import { serverTransportRaw } from "@/lib/api/transport.server";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ videoId: string }> },
) {
  const { videoId } = await params;
  const res = await serverTransportRaw(`/videos/${videoId}/stream`);

  if (!res.ok) {
    return new Response("Video not found", { status: res.status });
  }

  return new Response(res.body, {
    headers: {
      "Content-Type": res.headers.get("content-type") || "video/mp4",
      "Content-Length": res.headers.get("content-length") || "",
      "Accept-Ranges": res.headers.get("accept-ranges") || "bytes",
    },
  });
}
