import { PageItem, PaginatedPages, User, RefreshAllJob, AppConfig, SortField, SortOrder, Campaign, CampaignInput, RegistrationRequest, RegistrationSubmission } from "@/types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const BASE_URL = `${API_BASE_URL}/api/v1`;

let csrfTokenCache: string | null = null;
let onUnauthorizedCallback: (() => void) | null = null;

export function setOnUnauthorized(cb: () => void) {
  onUnauthorizedCallback = cb;
}

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
}

export async function fetchCsrfToken(): Promise<string> {
  const cookieToken = getCookie("csrf_token");
  if (cookieToken) {
    csrfTokenCache = cookieToken;
    return cookieToken;
  }
  const res = await fetch(`${BASE_URL}/auth/csrf`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch CSRF token");
  const data = await res.json();
  csrfTokenCache = data.csrf_token;
  return data.csrf_token;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  // Attach CSRF token on mutating requests
  if (["POST", "PUT", "DELETE", "PATCH"].includes(options.method?.toUpperCase() || "")) {
    const csrf = getCookie("csrf_token") || csrfTokenCache || (await fetchCsrfToken());
    if (csrf) {
      headers.set("X-CSRF-Token", csrf);
    }
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (response.status === 401) {
    if (onUnauthorizedCallback) {
      onUnauthorizedCallback();
    }
    const errData = await response.json().catch(() => ({}));
    const message = errData?.error?.message || "Session expired. Please sign in again.";
    const error = new Error(message);
    (error as any).status = 401;
    (error as any).code = errData?.error?.code || "UNAUTHENTICATED";
    throw error;
  }

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    const message = errData?.error?.message || response.statusText || "An unexpected error occurred.";
    const error = new Error(message);
    (error as any).status = response.status;
    (error as any).code = errData?.error?.code || "API_ERROR";
    throw error;
  }

  return response.json();
}

export const api = {
  // Auth
  getCsrf: fetchCsrfToken,
  login: (username: string, password: string) =>
    request<User>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  register: (username: string, password: string, contactEmail: string) =>
    request<RegistrationSubmission>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, contact_email: contactEmail }),
    }),
  getRegistrationRequests: () => request<RegistrationRequest[]>("/auth/registration-requests"),
  reviewRegistrationRequest: (requestId: string, decision: "approve" | "reject") =>
    request<RegistrationRequest>(`/auth/registration-requests/${requestId}/${decision}`, { method: "POST" }),
  logout: () =>
    request<{ message: string }>("/auth/logout", {
      method: "POST",
    }),
  getMe: () => request<User>("/auth/me"),

  // Config
  getConfig: () => request<AppConfig>("/config"),

  // Pages
  getPages: (sort: SortField = "followers", order: SortOrder = "desc", page = 1, search = "", pageSize = 50) => {
    const params = new URLSearchParams({ sort, order, page: String(page), page_size: String(pageSize) });
    if (search) params.set("q", search);
    return request<PaginatedPages>(`/pages?${params.toString()}`);
  },
  addPage: (username: string) =>
    request<PageItem>("/pages", {
      method: "POST",
      body: JSON.stringify({ username }),
    }),
  refreshPage: (pageId: string) =>
    request<PageItem>(`/pages/${pageId}/refresh`, {
      method: "POST",
    }),
  removePage: (pageId: string) =>
    request<{ message: string }>(`/pages/${pageId}`, {
      method: "DELETE",
    }),
  updatePageTags: (pageId: string, tags: string[]) =>
    request<PageItem>(`/pages/${pageId}/tags`, {
      method: "PUT",
      body: JSON.stringify({ tags }),
    }),
  refreshAllPages: () =>
    request<RefreshAllJob>("/pages/refresh-all", {
      method: "POST",
    }),
  getRefreshAllStatus: (jobId: string) =>
    request<RefreshAllJob>(`/pages/refresh-all/${jobId}`),
  getCurrentRefreshAll: () => request<RefreshAllJob | null>("/pages/refresh-all/current"),

  // Campaigns
  getCampaigns: () => request<Campaign[]>("/campaigns"),
  createCampaign: ({ name, description, page_ids }: CampaignInput) =>
    request<Campaign>("/campaigns", {
      method: "POST",
      body: JSON.stringify({ name, description: description || null, page_ids }),
    }),
  updateCampaign: ({ id, name, description, page_ids }: CampaignInput) =>
    request<Campaign>(`/campaigns/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name, description: description || null, page_ids }),
    }),
  removeCampaign: (campaignId: string) =>
    request<{ message: string }>(`/campaigns/${campaignId}`, { method: "DELETE" }),
};
