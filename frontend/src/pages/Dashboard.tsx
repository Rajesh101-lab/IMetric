import React, { useState } from "react";
import { TopBar } from "@/components/TopBar";
import { BottomNav, NavTab } from "@/components/BottomNav";
import { AddPageForm } from "@/components/AddPageForm";
import { SettingsSection } from "@/components/SettingsSection";
import { PagesTable } from "@/components/PagesTable";
import { useAuth } from "@/hooks/useAuth";
import { usePages, useRefreshPage, useRefreshAll } from "@/hooks/usePages";
import { SortField, SortOrder } from "@/types";
import { formatCompactNumber, formatPercent } from "@/lib/format";
import { Search, X } from "lucide-react";

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>("metrics");
  const [sortField, setSortField] = useState<SortField>("followers");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"cards" | "table">("cards");

  const { data: pages, isLoading, isError, refetch } = usePages(sortField, sortOrder);
  const refreshSingleMutation = useRefreshPage();
  const { startRefreshAll, isRunning: isRefreshingAll, jobStatus } = useRefreshAll();

  const handleSort = (field: SortField, order: SortOrder) => {
    setSortField(field);
    setSortOrder(order);
  };

  const handleRefreshSingle = (pageId: string) => {
    refreshSingleMutation.mutate(pageId);
  };

  const handleRefreshAll = async () => {
    try {
      await startRefreshAll();
    } catch (e) {
      // Handled via state
    }
  };

  const pagesList = pages || [];
  const filteredPages = searchQuery.trim()
    ? pagesList.filter((p) => p.username.toLowerCase().includes(searchQuery.toLowerCase().trim().replace(/^@/, "")))
    : pagesList;

  const totalPages = pagesList.length;
  const totalFollowers = pagesList.reduce((acc, p) => acc + p.followers, 0);
  const avgViewsPerFollower =
    totalPages > 0
      ? pagesList.reduce((acc, p) => acc + p.avg_views_per_follower, 0) / totalPages
      : 0;

  let progressText: string | null = null;
  if (isRefreshingAll && jobStatus) {
    progressText = `Refreshing ${jobStatus.done + jobStatus.failed}/${jobStatus.total}…`;
  }

  // Dynamic Header Title & Subtitle based on Active Tab
  const getHeaderInfo = () => {
    switch (activeTab) {
      case "add":
        return { title: "Add page", subtitle: "Track a new page you manage" };
      case "settings":
        return { title: "Settings", subtitle: "Account and preferences" };
      case "metrics":
      default:
        return {
          title: "Metrics",
          subtitle: searchQuery.trim()
            ? `${filteredPages.length} of ${totalPages} pages`
            : `${totalPages} pages you manage`,
        };
    }
  };

  const headerInfo = getHeaderInfo();

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 pb-32 pt-2">
      {/* Top Header */}
      <TopBar
        title={headerInfo.title}
        subtitle={headerInfo.subtitle}
        onRefreshAll={activeTab === "metrics" ? handleRefreshAll : undefined}
        isRefreshing={isRefreshingAll}
      />

      {/* Main Content View Switcher */}
      <main className="space-y-6">
        {/* 1. ADD PAGE TAB */}
        {activeTab === "add" && <AddPageForm />}

        {/* 2. SETTINGS TAB */}
        {activeTab === "settings" && <SettingsSection username={user?.username} />}

        {/* 3. METRICS DASHBOARD TAB */}
        {activeTab === "metrics" && (
          <>
            {/* KPI Cards (3 Columns) */}
            <div className="app-card grid grid-cols-3 divide-x divide-[var(--line)] overflow-hidden">
              <div className="p-4 sm:p-5">
                <span className="text-xs text-[var(--mut)] block">Pages tracked</span>
                <b className="block font-bold text-2xl sm:text-3xl text-[var(--ink)] tracking-tight mt-1 tabular-nums">
                  {formatCompactNumber(totalPages)}
                </b>
              </div>

              <div className="p-4 sm:p-5">
                <span className="text-xs text-[var(--mut)] block">Total followers</span>
                <b className="block font-bold text-2xl sm:text-3xl text-[var(--ink)] tracking-tight mt-1 tabular-nums">
                  {formatCompactNumber(totalFollowers)}
                </b>
              </div>

              <div className="p-4 sm:p-5">
                <span className="text-xs text-[var(--mut)] block">Avg views / follower</span>
                <b className="block font-bold text-2xl sm:text-3xl text-[var(--ink)] tracking-tight mt-1 tabular-nums">
                  {formatPercent(avgViewsPerFollower)}
                </b>
              </div>
            </div>

            {/* Search Input Bar */}
            <div className="flex items-center gap-2.5 h-12 px-4 rounded-full bg-[var(--card)] border border-[var(--line)] text-[var(--mut)] focus-within:border-[var(--cof)] transition-colors">
              <Search className="w-5 h-5 flex-none text-[var(--mut)]" />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search pages by username"
                autoComplete="off"
                className="flex-1 min-w-0 bg-transparent border-0 outline-none text-[var(--ink)] text-sm sm:text-base placeholder-[var(--mut)]"
                aria-label="Search pages"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  aria-label="Clear search"
                  className="text-[var(--mut)] hover:text-[var(--ink)] p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Pages List & Controls */}
            <PagesTable
              pages={filteredPages}
              isLoading={isLoading}
              isError={isError}
              refetch={refetch}
              currentSort={sortField}
              currentOrder={sortOrder}
              onSort={handleSort}
              onRefreshSingle={handleRefreshSingle}
              refreshingPageId={refreshSingleMutation.isPending ? refreshSingleMutation.variables : null}
              onRefreshAll={handleRefreshAll}
              isRefreshingAll={isRefreshingAll}
              refreshAllProgressText={progressText}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
            />
          </>
        )}
      </main>

      {/* Floating Bottom Navigation Dock */}
      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
};
