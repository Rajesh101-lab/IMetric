import React from "react";
import { RefreshCw, Sun, Moon, UserRound } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

interface TopBarProps {
  username?: string;
  onRefreshAll?: () => void;
  isRefreshing?: boolean;
  onAccountClick?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  username,
  onRefreshAll,
  isRefreshing,
  onAccountClick,
}) => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <header className="workspace-topbar">
      <div className="workspace-topbar-inner">
        <div className="workspace-actions" role="toolbar" aria-label="Workspace actions">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle dark mode"
            className="icon-btn"
            title="Toggle dark mode"
          >
            {isDark ? <Sun className="w-5 h-5 text-[var(--cof)]" /> : <Moon className="w-5 h-5" />}
          </button>
          {onRefreshAll && (
            <button
              type="button"
              onClick={onRefreshAll}
              disabled={isRefreshing}
              aria-label="Refresh all pages"
              className="app-btn workspace-refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-[var(--cof)]" : ""}`} />
              <span>{isRefreshing ? "Refreshing…" : "Refresh all"}</span>
            </button>
          )}
          <button
            type="button"
            onClick={onAccountClick}
            aria-label={username ? `Account settings for ${username}` : "Account settings"}
            title={username || "Account settings"}
            className="icon-btn"
          >
            <UserRound className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
};
