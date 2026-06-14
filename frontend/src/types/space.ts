/**
 * TypeScript interfaces for the Spaces feature.
 */

export interface Space {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  icon: string;
  color: string;
  content_count: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  last_accessed_at: string | null;
}

export interface SpaceListItem {
  id: number;
  name: string;
  icon: string;
  color: string;
  content_count: number;
  is_public: boolean;
  last_accessed_at: string | null;
}

export interface ExploreSpaceItem {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  icon: string;
  color: string;
  content_count: number;
  owner_username: string | null;
  created_at: string;
}

export interface SpaceCreatePayload {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  is_public?: boolean;
}

export interface SpaceUpdatePayload {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  is_public?: boolean;
}
