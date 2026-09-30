import React from "react";
import { RefreshCw, Sun, Moon } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

interface TopBarProps {
  title: string;
  subtitle: string;
  onRefreshAll?: () => void;
  isRefreshing?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  title,
  subtitle,
  onRefreshAll,
  isRefreshing,
}) => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <header className="w-full flex items-end justify-between my-4 mb-6 gap-3">
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--ink)]">
          {title}
        </h1>
        <p className="text-sm font-medium text-[var(--mut)] mt-1.5">
          {subtitle}
        </p>
      </div>

      <div className="flex items-center gap-2">
        {onRefreshAll && (
          <button
            type="button"
            onClick={onRefreshAll}
            disabled={isRefreshing}
            aria-label="Refresh all pages"
            className="app-btn"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-[var(--cof)]" : ""}`} />
            <span className="hidden sm:inline">
              {isRefreshing ? "Refreshing…" : "Refresh all"}
            </span>
          </button>
        )}

        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle dark mode"
          className="icon-btn"
          title="Toggle dark mode"
        >
          {isDark ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>
    </header>
  );
};
