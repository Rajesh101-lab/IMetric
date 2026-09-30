import React, { useState } from "react";
import { Server, Check } from "lucide-react";
import { LogoutButton } from "./LogoutButton";
import { useTheme, Theme } from "@/hooks/useTheme";
import { useConfig } from "@/hooks/usePages";

interface SettingsSectionProps {
  username?: string;
}

export const SettingsSection: React.FC<SettingsSectionProps> = ({ username }) => {
  const { theme, toggleTheme } = useTheme();
  const { data: configData } = useConfig();

  const [serverUrl, setServerUrl] = useState(() => localStorage.getItem("server_url") || "http://10.0.2.2:8000");
  const [tempUrl, setTempUrl] = useState(serverUrl);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSaveServer = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = tempUrl.trim();
    localStorage.setItem("server_url", trimmed);
    setServerUrl(trimmed);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

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

      {/* Data & Server Group */}
      <div className="app-card p-5 sm:p-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--mut)] mb-3">
          Data & Server
        </h3>

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
              <b className="font-semibold text-sm text-[var(--ink)] block">Backup source</b>
              <span className="text-xs text-[var(--mut)]">Secondary data provider when Meta Graph API fails</span>
            </div>
            <span className="text-sm font-bold text-[var(--ink)]">
              {isBackupEnabled ? "On" : "Off"}
            </span>
          </div>

          {/* Server Config */}
          <div className="pt-4 pb-1">
            <b className="font-semibold text-sm text-[var(--ink)] block mb-1">
              Backend Server Endpoint
            </b>
            <p className="text-xs text-[var(--mut)] mb-3">
              API server for fetching social media metrics ({serverUrl}).
            </p>

            <form onSubmit={handleSaveServer} className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <Server className="w-4 h-4 text-[var(--mut)] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={tempUrl}
                    onChange={(e) => setTempUrl(e.target.value)}
                    placeholder="http://10.0.2.2:8000"
                    className="w-full pl-10 pr-4 py-2.5 rounded-full border border-[var(--line)] bg-[var(--bg)] text-[var(--ink)] text-sm focus:outline-none focus:border-[var(--cof)]"
                  />
                </div>

                <button
                  type="submit"
                  className="app-btn h-10 px-5 text-xs font-bold"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Save</span>
                </button>
              </div>

              {savedSuccess && (
                <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                  ✓ Endpoint saved successfully
                </p>
              )}
            </form>
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-[var(--mut)] font-medium pt-2">
        Page Metrics App • Version 3.0.0
      </div>
    </div>
  );
};
