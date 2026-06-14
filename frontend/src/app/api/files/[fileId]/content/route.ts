import { NextRequest } from "next/server";
import { serverTransportRaw } from "@/lib/api/transport.server";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ fileId: string }> },
) {
  const { fileId } = await params;
  const res = await serverTransportRaw(`/materials/files/${fileId}/content`);

  if (!res.ok) {
    return new Response("File not found", { status: res.status });
  }

  return new Response(res.body, {
    headers: {
      "Content-Type":
        res.headers.get("content-type") || "application/octet-stream",
      "Content-Disposition": res.headers.get("content-disposition") || "inline",
    },
  });
}
