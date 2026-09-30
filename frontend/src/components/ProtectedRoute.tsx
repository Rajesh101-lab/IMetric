import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Loader2 } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, isLoading, isError } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen w-full flex flex-col items-center justify-center p-4 bg-[var(--bg)] text-[var(--ink)]">
        <Loader2 className="w-10 h-10 animate-spin text-[var(--cof)] mb-4" />
        <p className="text-sm font-semibold text-[var(--mut)]">
          Loading workspace…
        </p>
      </div>
    );
  }

  if (isError || !user) {
    return <Navigate to="/login?expired=true" replace />;
  }

  return <>{children}</>;
};
