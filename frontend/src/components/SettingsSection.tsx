import React from "react";
import { LogoutButton } from "./LogoutButton";
import { useTheme, Theme } from "@/hooks/useTheme";
import { useConfig } from "@/hooks/usePages";

interface SettingsSectionProps {
  username?: string;
}

export const SettingsSection: React.FC<SettingsSectionProps> = ({ username }) => {
  const { theme, toggleTheme } = useTheme();
  const { data: configData } = useConfig();

  const handleThemeChange = (selectedTheme: Theme) => {
    if (theme !== selectedTheme) {
      toggleTheme();
    }
  };

  const isBackupEnabled = configData?.backup_enabled ?? false;

  return (
    <div className="space-y-6 pb-24">
      {/* Account Group */}
      <div className="app-card p-5 sm:p-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--mut)] mb-3">
          Account
        </h3>

        <div className="divide-y divide-[var(--line)]">
          <div className="flex items-center justify-between py-3.5 first:pt-0">
            <div>
              <b className="font-semibold text-sm text-[var(--ink)] block">Agency ID</b>
              <span className="text-xs text-[var(--mut)]">Signed in</span>
            </div>
            <span className="font-bold text-base text-[var(--ink)]">
              {username || "agency_admin"}
            </span>
          </div>

          <div className="flex items-center justify-between py-3.5 last:pb-0">
            <div>
              <b className="font-semibold text-sm text-[var(--ink)] block">Session</b>
              <span className="text-xs text-[var(--mut)]">Active session</span>
            </div>
            <LogoutButton />
          </div>
        </div>
      </div>

      {/* Appearance Group */}
      <div className="app-card p-5 sm:p-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--mut)] mb-3">
          Appearance
        </h3>

        <div className="flex items-center justify-between py-2">
          <div>
            <b className="font-semibold text-sm text-[var(--ink)] block">Theme</b>
            <span className="text-xs text-[var(--mut)]">Customize dark or light mode</span>
          </div>

          <div className="segmented-control">
            <button
              type="button"
              onClick={() => handleThemeChange("light")}
              aria-pressed={theme === "light"}
            >
              Light
            </button>
            <button
              type="button"
              onClick={() => handleThemeChange("dark")}
              aria-pressed={theme === "dark"}
            >
              Dark
            </button>
          </div>
        </div>
      </div>

      {/* Data Group */}
      <div className="app-card p-5 sm:p-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--mut)] mb-3">Data</h3>

        <div className="divide-y divide-[var(--line)]">
          <div className="flex items-center justify-between py-3.5 first:pt-0">
            <div>
              <b className="font-semibold text-sm text-[var(--ink)] block">Metrics sample</b>
              <span className="text-xs text-[var(--mut)]">Most recent reels used for averages</span>
            </div>
            <span className="text-sm font-semibold text-[var(--ink)]">12 reels</span>
          </div>

          <div className="flex items-center justify-between py-3.5">
            <div>
              <b className="font-semibold text-sm text-[var(--ink)] block">Refresh limit</b>
              <span className="text-xs text-[var(--mut)]">One refresh per page each minute</span>
            </div>
            <span className="text-sm font-semibold text-[var(--ink)]">60s</span>
          </div>

          <div className="flex items-center justify-between py-3.5">
            <div>
              <b className="font-semibold text-sm text-[var(--ink)] block">Official Graph API</b>
              <span className="text-xs text-[var(--mut)]">
                {configData?.official_api_configured
                  ? "Credentials configured; Meta access is checked on fetch."
                  : "Meta access token and Instagram account ID are missing."}
              </span>
            </div>
            <span className="text-sm font-bold text-[var(--ink)]">
              {configData?.official_api_configured ? "Configured" : "Missing"}
            </span>
          </div>

          <div className="flex items-center justify-between py-3.5">
            <div>
              <b className="font-semibold text-sm text-[var(--ink)] block">SerpApi fallback</b>
              <span className="text-xs text-[var(--mut)]">Used only after an eligible Meta error</span>
            </div>
            <span className="text-sm font-bold text-[var(--ink)]">
              {isBackupEnabled ? "On" : "Off"}
            </span>
          </div>

        </div>
      </div>

      <div className="text-center text-xs text-[var(--mut)] font-medium pt-2">
        IMetric • Web workspace
      </div>
    </div>
  );
};
