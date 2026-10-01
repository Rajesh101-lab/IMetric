export interface User {
  id: string;
  username: string;
  is_admin: boolean;
}

export interface RegistrationRequest {
  id: string;
  username: string;
  contact_email: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface RegistrationSubmission {
  username: string;
  status: "pending";
}

export interface PageItem {
  id: string;
  username: string;
  tags: string[];
  status: 'pending' | 'ready' | 'failed';
  source: 'official' | 'backup';
  fallback_reason: string | null;
  error_kind: string | null;
  error_message: string | null;
  followers: number;
  last_reel_likes: number | null;
  last_reel_views: number | null;
  avg_views: number;
  median_views: number;
  avg_likes: number;
  like_to_view_ratio: number;
  avg_views_per_follower: number;
  reels_sampled: number;
  last_refreshed_at: string | null;
  last_refresh_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface PageSummary {
  total_pages: number;
  total_followers: number;
  avg_views_per_follower: number;
}

export interface PaginatedPages {
  items: PageItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  summary: PageSummary;
}

export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  page_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface CampaignInput {
  id?: string;
  name: string;
  description: string;
  page_ids: string[];
}

export interface RefreshAllJob {
  job_id: string;
  total: number;
  done: number;
  failed: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
}

export interface AppConfig {
  backup_enabled: boolean;
  official_api_configured: boolean;
}

export type SortField =
  | 'username'
  | 'followers'
  | 'last_reel_likes'
  | 'last_reel_views'
  | 'avg_views'
  | 'median_views'
  | 'avg_likes'
  | 'like_to_view_ratio'
  | 'avg_views_per_follower'
  | 'last_refreshed_at'
  | 'created_at';

export type SortOrder = 'asc' | 'desc';

export interface ApiError {
  code: string;
  message: string;
}
