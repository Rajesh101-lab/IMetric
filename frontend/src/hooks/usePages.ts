import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageItem, SortField, SortOrder, RefreshAllJob, AppConfig } from "@/types";

export function usePages(sort: SortField = "followers", order: SortOrder = "desc") {
  return useQuery<PageItem[], Error>({
    queryKey: ["pages", sort, order],
    queryFn: () => api.getPages(sort, order),
    staleTime: 30 * 1000,
    refetchInterval: (query) => {
      const pagesList = query.state.data;
      if (pagesList && pagesList.some((p) => p.status === "pending")) {
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

export function useAddPage() {
  const queryClient = useQueryClient();

  return useMutation<PageItem, Error, string>({
    mutationFn: (username: string) => api.addPage(username),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pages"] });
    },
  });
}

export function useRefreshPage() {
  const queryClient = useQueryClient();

  return useMutation<PageItem, Error, string>({
    mutationFn: (pageId: string) => api.refreshPage(pageId),
    onSuccess: (updatedPage) => {
      queryClient.setQueriesData<PageItem[]>({ queryKey: ["pages"] }, (oldPages) => {
        if (!oldPages) return [updatedPage];
        return oldPages.map((p) => (p.id === updatedPage.id ? updatedPage : p));
      });
      queryClient.invalidateQueries({ queryKey: ["pages"] });
    },
  });
}

export function useRefreshAll() {
  const queryClient = useQueryClient();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

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

  const isRunning = startMutation.isPending || (statusQuery.data?.status === "running");
  const jobStatus = statusQuery.data || startMutation.data || null;

  return {
    startRefreshAll: startMutation.mutateAsync,
    isRunning,
    jobStatus,
    error: startMutation.error || statusQuery.error,
  };
}
