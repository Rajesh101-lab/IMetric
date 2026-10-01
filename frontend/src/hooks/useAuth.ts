import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { RegistrationRequest } from "@/types";

export function useAuth() {
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => api.getMe(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const loginMutation = useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      api.login(username, password),
    onSuccess: (data) => {
      queryClient.setQueryData(["auth", "me"], data);
      queryClient.invalidateQueries({ queryKey: ["pages"] });
    },
  });

  const registerMutation = useMutation({
    mutationFn: ({ username, password, contactEmail }: { username: string; password: string; contactEmail: string }) =>
      api.register(username, password, contactEmail),
  });

  const logoutMutation = useMutation({
    mutationFn: () => api.logout(),
    onSuccess: () => {
      queryClient.clear();
      queryClient.setQueryData(["auth", "me"], null);
    },
  });

  return {
    user: meQuery.data || null,
    isLoading: meQuery.isLoading,
    isError: meQuery.isError,
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    register: registerMutation.mutateAsync,
    isRegistering: registerMutation.isPending,
    registerError: registerMutation.error,
    logout: logoutMutation.mutateAsync,
    isLoggingOut: logoutMutation.isPending,
  };
}

export function useRegistrationRequests() {
  return useQuery<RegistrationRequest[], Error>({
    queryKey: ["registration-requests"],
    queryFn: () => api.getRegistrationRequests(),
  });
}

export function useReviewRegistrationRequest() {
  const queryClient = useQueryClient();
  return useMutation<RegistrationRequest, Error, { requestId: string; decision: "approve" | "reject" }>({
    mutationFn: ({ requestId, decision }) => api.reviewRegistrationRequest(requestId, decision),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["registration-requests"] }),
  });
}
