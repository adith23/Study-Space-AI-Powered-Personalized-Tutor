export interface UploadedFileState {
  id: number;
  name: string;
  status: "pending" | "processing" | "success" | "failed";
}

export interface UploadedFileUploadResponse {
  id: number;
  name: string;
  status?: UploadedFileState["status"];
}

export interface UploadedFileListResponse {
  id: number;
  name: string | null;
  status: string;
}

export interface ChatSession {
  id: string;
  name: string;
}

export interface ChatMessage {
  role: "human" | "ai";
  content: string;
}
