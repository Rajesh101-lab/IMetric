import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageItem, PaginatedPages, SortField, SortOrder, RefreshAllJob, AppConfig, Campaign, CampaignInput } from "@/types";

export function usePages(sort: SortField = "followers", order: SortOrder = "desc", page = 1, search = "") {
  return useQuery<PaginatedPages, Error>({
    queryKey: ["pages", sort, order, page, search],
    queryFn: () => api.getPages(sort, order, page, search),
    staleTime: 30 * 1000,
    refetchInterval: (query) => {
      const pagesList = query.state.data;
      if (pagesList?.items.some((item) => item.status === "pending")) {
        return 2000;
      }
      return false;
    },
  });
}

export function useConfig() {
  return useQuery<AppConfig, Error>({
    queryKey: ["config"],
    queryFn: () => api.getConfig(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAllPages(enabled = true) {
  return useQuery<PageItem[], Error>({
    queryKey: ["all-pages"],
    queryFn: async () => {
      const first = await api.getPages("username", "asc", 1, "", 200);
      const pages = [...first.items];
      for (let start = 2; start <= first.total_pages; start += 4) {
        const pageNumbers = Array.from({ length: Math.min(4, first.total_pages - start + 1) }, (_, index) => start + index);
        const batches = await Promise.all(pageNumbers.map((page) => api.getPages("username", "asc", page, "", 200)));
        pages.push(...batches.flatMap((batch) => batch.items));
      }
      return pages;
    },
    enabled,
    staleTime: 30 * 1000,
  });
}

export function useAddPage() {
  const queryClient = useQueryClient();

  return useMutation<PageItem, Error, string>({
    mutationFn: (username: string) => api.addPage(username),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pages"] });
      queryClient.invalidateQueries({ queryKey: ["all-pages"] });
    },
  });
}

export function useRefreshPage() {
  const queryClient = useQueryClient();

  return useMutation<PageItem, Error, string>({
    mutationFn: (pageId: string) => api.refreshPage(pageId),
    onSuccess: (updatedPage) => {
      queryClient.setQueriesData<PaginatedPages>({ queryKey: ["pages"] }, (oldPages) => {
        if (!oldPages) return oldPages;
        return { ...oldPages, items: oldPages.items.map((p) => (p.id === updatedPage.id ? updatedPage : p)) };
      });
      queryClient.invalidateQueries({ queryKey: ["pages"] });
    },
  });
}

export function useRemovePage() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: (pageId: string) => api.removePage(pageId),
    onSuccess: (_result, pageId) => {
      queryClient.setQueriesData<PaginatedPages>({ queryKey: ["pages"] }, (pages) =>
        pages ? { ...pages, items: pages.items.filter((page) => page.id !== pageId), total: Math.max(0, pages.total - 1), total_pages: Math.ceil(Math.max(0, pages.total - 1) / pages.page_size), summary: { ...pages.summary, total_pages: Math.max(0, pages.summary.total_pages - 1) } } : pages
      );
      queryClient.invalidateQueries({ queryKey: ["pages"] });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      queryClient.invalidateQueries({ queryKey: ["all-pages"] });
    },
  });
}

export function useUpdatePageTags() {
  const queryClient = useQueryClient();
  return useMutation<PageItem, Error, { pageId: string; tags: string[] }>({
    mutationFn: ({ pageId, tags }) => api.updatePageTags(pageId, tags),
    onSuccess: (updatedPage) => {
      queryClient.setQueriesData<PaginatedPages>({ queryKey: ["pages"] }, (oldPages) =>
        oldPages ? { ...oldPages, items: oldPages.items.map((page) => (page.id === updatedPage.id ? updatedPage : page)) } : oldPages
      );
      queryClient.invalidateQueries({ queryKey: ["pages"] });
    },
  });
}

export function useCampaigns() {
  return useQuery<Campaign[], Error>({
    queryKey: ["campaigns"],
    queryFn: () => api.getCampaigns(),
    staleTime: 30 * 1000,
  });
}

export function useSaveCampaign() {
  const queryClient = useQueryClient();
  return useMutation<Campaign, Error, CampaignInput>({
    mutationFn: (input) => input.id ? api.updateCampaign(input) : api.createCampaign(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["campaigns"] }),
  });
}

export function useRemoveCampaign() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string }, Error, string>({
    mutationFn: (campaignId) => api.removeCampaign(campaignId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["campaigns"] }),
  });
}

export function useRefreshAll() {
  const queryClient = useQueryClient();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const currentJobQuery = useQuery<RefreshAllJob | null, Error>({
    queryKey: ["refresh-all", "current"],
    queryFn: () => api.getCurrentRefreshAll(),
    staleTime: 0,
  });

  useEffect(() => {
    if (currentJobQuery.data?.job_id) setActiveJobId(currentJobQuery.data.job_id);
  }, [currentJobQuery.data?.job_id]);

  const startMutation = useMutation<RefreshAllJob, Error, void>({
    mutationFn: () => api.refreshAllPages(),
    onSuccess: (job) => {
      setActiveJobId(job.job_id);
    },
  });

  const statusQuery = useQuery<RefreshAllJob, Error>({
    queryKey: ["refresh-all", activeJobId],
    queryFn: () => api.getRefreshAllStatus(activeJobId!),
    enabled: !!activeJobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === "completed" || data.status === "failed")) {
        queryClient.invalidateQueries({ queryKey: ["pages"] });
        return false;
      }
      return 2000;
    },
  });

  const isRunning = startMutation.isPending || statusQuery.data?.status === "queued" || statusQuery.data?.status === "running" || currentJobQuery.data?.status === "queued" || currentJobQuery.data?.status === "running";
  const jobStatus = statusQuery.data || startMutation.data || currentJobQuery.data || null;

  return {
    startRefreshAll: startMutation.mutateAsync,
    isRunning,
    jobStatus,
    error: startMutation.error || statusQuery.error,
  };
}
