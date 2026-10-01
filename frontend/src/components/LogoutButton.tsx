import React from "react";
import { LogOut, Loader2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useNavigate } from "react-router-dom";

export const LogoutButton: React.FC = () => {
  const { logout, isLoggingOut } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (e) {
      navigate("/login");
    }
  };

  return (
    <button
      type="button"
      onClick={handleLogout}
      disabled={isLoggingOut}
      aria-label="Sign out"
      title="Sign out of agency account"
      className="app-btn ghost workspace-logout-button text-xs font-semibold"
    >
      {isLoggingOut ? (
        <Loader2 className="w-4 h-4 animate-spin text-[var(--mut)]" />
      ) : (
        <>
          <LogOut className="w-4 h-4" />
          <span>Sign out</span>
        </>
      )}
    </button>
  );
};
