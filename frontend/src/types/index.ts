export interface Material {
  id: number;
  title: string;
  description?: string;
  type: 'note' | 'syllabus' | 'pdf' | 'book' | 'video' | 'link';
  content?: string;
  file_path?: string;
  url?: string;
  metadata?: Record<string, any>;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  learning_style?: string;
  difficulty_level?: string;
  preferences?: Record<string, any>;
} 

export interface UploadResponse {
  id: number;
  name: string;
  stored_path?: string;
  url?: string; 
  file_type: string;
  status: string;
}

export interface StatusResponse {
  id: number;
  name: string;
  status: "pending" | "processing" | "success" | "failed";
  error_message?: string;
}