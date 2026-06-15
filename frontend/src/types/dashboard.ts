export interface UploadedFileState {
  id: number;
  name: string;
  status: "pending" | "processing" | "success" | "failed";
  error?: string;
}

export interface UploadedFileUploadResponse {
  id: number;
  name: string;
  status?: UploadedFileState["status"];
  error_message?: string;
}

export interface UploadedFileListResponse {
  id: number;
  name: string | null;
  status: string;
  error_message?: string;
}

export interface ChatSession {
  id: string;
  name: string;
}

export interface ChatMessage {
  role: "human" | "ai";
  content: string;
}
