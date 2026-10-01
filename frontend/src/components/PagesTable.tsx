import React, { useState } from "react";
import { RefreshCw, AlertCircle, LayoutGrid, Table as TableIcon, ArrowDown, ChevronLeft, ChevronRight, Trash2 } from "lucide-react";
import { PageItem, SortField, SortOrder } from "@/types";
import { PageCard } from "./PageCard";
import { PageTagsEditor } from "./PageTagsEditor";
import { ConfirmDialog } from "./ConfirmDialog";
import { TableSkeleton } from "./Skeletons";
import { useRemovePage } from "@/hooks/usePages";
import {
  formatCompactNumber,
  formatPercent,
  formatRelativeTime,
  formatNumberWithCommas,
} from "@/lib/format";

interface PagesTableProps {
  pages: PageItem[] | undefined;
  isLoading: boolean;
  isError: boolean;
  refetch: () => void;
  currentSort: SortField;
  currentOrder: SortOrder;
  onSort: (field: SortField, order: SortOrder) => void;
  onRefreshSingle: (id: string) => void;
  refreshingPageId?: string | null;
  onRefreshAll: () => void;
  isRefreshingAll: boolean;
  refreshAllProgressText?: string | null;
  viewMode: "cards" | "table";
  onViewModeChange: (mode: "cards" | "table") => void;
  page: number;
  totalPages: number;
  totalResults: number;
  onPageChange: (page: number) => void;
  hasSearch: boolean;
}

const SORT_CHIPS: { field: SortField; label: string }[] = [
  { field: "followers", label: "Followers" },
  { field: "last_reel_likes", label: "Last reel likes" },
  { field: "last_reel_views", label: "Last reel views" },
  { field: "avg_views", label: "Avg views" },
  { field: "median_views", label: "Median views" },
  { field: "avg_likes", label: "Avg likes" },
  { field: "like_to_view_ratio", label: "Like / view" },
  { field: "avg_views_per_follower", label: "Views / followers" },
];

export const PagesTable: React.FC<PagesTableProps> = ({
  pages,
  isLoading,
  isError,
  refetch,
  currentSort,
  currentOrder,
  onSort,
  onRefreshSingle,
  refreshingPageId,
  viewMode,
  onViewModeChange,
  page,
  totalPages,
  totalResults,
  onPageChange,
  hasSearch,
}) => {
  const [localRefreshingId, setLocalRefreshingId] = useState<string | null>(null);
  const [pageToDelete, setPageToDelete] = useState<PageItem | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const removeMutation = useRemovePage();

  const handleRefreshClick = (id: string) => {
    setLocalRefreshingId(id);
    onRefreshSingle(id);
    setTimeout(() => setLocalRefreshingId(null), 1500);
  };

  const handleDeleteClick = (page: PageItem) => {
    setDeleteError(null);
    setPageToDelete(page);
  };

  const handleConfirmDelete = async () => {
    if (!pageToDelete) return;
    setDeleteError(null);
    try {
      await removeMutation.mutateAsync(pageToDelete.id);
      setPageToDelete(null);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Could not remove this page.");
    }
  };

  const handleChipClick = (field: SortField) => {
    if (currentSort === field) {
      onSort(field, currentOrder === "asc" ? "desc" : "asc");
    } else {
      onSort(field, "desc");
    }
  };

  if (isLoading) return <TableSkeleton />;

  if (isError) {
    return (
      <div className="app-card p-12 text-center flex flex-col items-center justify-center">
        <AlertCircle className="w-12 h-12 text-[var(--cof)] mb-4" />
        <h3 className="text-xl font-bold text-[var(--ink)] mb-2">
          Couldn't load page metrics
        </h3>
        <p className="text-[var(--mut)] mb-6 text-sm">
          There was an error communicating with the server. Please check your connection and try again.
        </p>
        <button
          onClick={() => refetch()}
          className="app-btn"
        >
          Retry
        </button>
      </div>
    );
  }

  const pagesList = pages || [];
  const hasPages = pagesList.length > 0;

  return (
    <div className="space-y-4">
      {/* Bar with Sort Chips & Segmented Cards/Table View Control */}
      <div className="flex items-center gap-3 my-3">
        {/* Horizontal Scrolling Chips */}
        <div className="flex gap-2 overflow-x-auto flex-1 py-1 no-scrollbar" role="group" aria-label="Sort by">
          {SORT_CHIPS.map((chip) => {
            const isActive = currentSort === chip.field;
            return (
              <button
                key={chip.field}
                type="button"
                onClick={() => handleChipClick(chip.field)}
                aria-pressed={isActive}
                className="chip-btn"
              >
                    <span>{chip.label}</span>
                {isActive && (
                  <span className={`inline-flex transition-transform duration-200 ${currentOrder === "asc" ? "rotate-180" : ""}`}>
                    <ArrowDown className="w-3.5 h-3.5" />
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* View Segmented Toggle */}
        <div className="segmented-control flex-none">
          <button
            type="button"
            onClick={() => onViewModeChange("cards")}
            aria-pressed={viewMode === "cards"}
            aria-label="Card view"
          >
            <LayoutGrid className="w-4 h-4" />
            <span className="hidden sm:inline">Cards</span>
          </button>
          <button
            type="button"
            onClick={() => onViewModeChange("table")}
            aria-pressed={viewMode === "table"}
            aria-label="Table view"
          >
            <TableIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Table</span>
          </button>
        </div>
      </div>

      {!hasPages ? (
        <div className="app-card p-12 text-center flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-full bg-[var(--cofs)] text-[var(--cof)] flex items-center justify-center text-2xl mb-4">
            📊
          </div>
          <h3 className="text-xl font-bold text-[var(--ink)] mb-1">
            {hasSearch ? "No matching pages" : "No pages tracked yet"}
          </h3>
          <p className="text-[var(--mut)] text-sm max-w-sm">
            {hasSearch ? "Try another username or tag." : "Add a page to start tracking performance."}
          </p>
        </div>
      ) : viewMode === "cards" ? (
        /* Cards Grid View */
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {pagesList.map((page) => (
            <PageCard
              key={page.id}
              page={page}
              onRefresh={handleRefreshClick}
              isRefreshing={refreshingPageId === page.id || localRefreshingId === page.id}
            />
          ))}
        </div>
      ) : (
        /* Table View */
        <div className="app-card overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm min-w-[1040px]">
            <thead>
              <tr className="border-b border-[var(--line)]">
                <th scope="col" className="py-3.5 px-4 text-left bg-[var(--card)] sticky left-0 z-20">
                  <button
                    type="button"
                    onClick={() => handleChipClick("username")}
                    className="font-semibold text-xs text-[var(--mut)] hover:text-[var(--ink)]"
                  >
                    PAGE
                  </button>
                </th>
                <th scope="col" className="py-3.5 px-3 text-left bg-[var(--card)] font-semibold text-xs text-[var(--mut)]">TAGS</th>
                {SORT_CHIPS.map((chip) => (
                  <th key={chip.field} scope="col" className="py-3.5 px-3 text-right bg-[var(--card)]">
                    <button
                      type="button"
                      onClick={() => handleChipClick(chip.field)}
                      className={`inline-flex items-center gap-1 font-semibold text-xs ml-auto ${
                        currentSort === chip.field ? "text-[var(--ink)]" : "text-[var(--mut)] hover:text-[var(--ink)]"
                      }`}
                    >
                      <span>{chip.label.toUpperCase()}</span>
                      {currentSort === chip.field && (currentOrder === "asc" ? " ↑" : " ↓")}
                    </button>
                  </th>
                ))}
                <th scope="col" className="py-3.5 px-4 text-right bg-[var(--card)] font-semibold text-xs text-[var(--mut)]">
                  UPDATED
                </th>
                <th scope="col" className="py-3.5 px-3 bg-[var(--card)]"></th>
                <th scope="col" className="py-3.5 px-3 bg-[var(--card)]"></th>
              </tr>
            </thead>

            <tbody className="divide-y divide-[var(--line)]">
              {pagesList.map((page) => {
                const initial = page.username.charAt(0).toUpperCase();
                const isItemRefreshing = refreshingPageId === page.id || localRefreshingId === page.id;

                return (
                  <tr
                    key={page.id}
                    className={`hover:bg-[var(--bg)] transition-colors ${
                      isItemRefreshing ? "opacity-60" : ""
                    }`}
                  >
                    {/* Sticky Page Username */}
                    <td className="py-3.5 px-4 sticky left-0 z-10 bg-[var(--card)]">
                      <div className="flex items-center gap-3 font-semibold text-[var(--ink)]">
                        <div className="w-8 h-8 rounded-full bg-[var(--ink)] text-[var(--card)] flex items-center justify-center text-xs font-bold">
                          {initial}
                        </div>
                        <div>
                          <div className="hover:underline cursor-pointer">@{page.username}</div>
                          {page.last_refresh_error && (
                            <div className="text-[11px] font-normal text-[var(--cof)] flex items-center gap-1 mt-0.5">
                              <AlertCircle className="w-3 h-3 flex-shrink-0" />
                              <span>{page.last_refresh_error}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-3 min-w-[180px]"><PageTagsEditor page={page} /></td>

                    {/* Followers */}
                    <td className="py-3.5 px-3 text-right tabular-nums text-[var(--ink)] font-medium" title={formatNumberWithCommas(page.followers)}>
                      {formatCompactNumber(page.followers)}
                    </td>

                    {/* Last Reel Likes */}
                    <td className="py-3.5 px-3 text-right tabular-nums text-[var(--ink)]" title={formatNumberWithCommas(page.last_reel_likes)}>
                      {page.last_reel_likes !== null ? formatCompactNumber(page.last_reel_likes) : "—"}
                    </td>

                    {/* Last Reel Views */}
                    <td className="py-3.5 px-3 text-right tabular-nums text-[var(--ink)]" title={formatNumberWithCommas(page.last_reel_views)}>
                      {page.last_reel_views !== null ? formatCompactNumber(page.last_reel_views) : "—"}
                    </td>

                    {/* Avg Views */}
                    <td className="py-3.5 px-3 text-right tabular-nums text-[var(--ink)] font-medium" title={formatNumberWithCommas(page.avg_views)}>
                      {formatCompactNumber(page.avg_views)}
                    </td>

                    {/* Median Views */}
                    <td className="py-3.5 px-3 text-right tabular-nums text-[var(--ink)]" title={formatNumberWithCommas(page.median_views)}>
                      {formatCompactNumber(page.median_views)}
                    </td>

                    {/* Avg Likes */}
                    <td className="py-3.5 px-3 text-right tabular-nums text-[var(--ink)]" title={formatNumberWithCommas(page.avg_likes)}>
                      {formatCompactNumber(page.avg_likes)}
                    </td>

                    {/* Like / View % */}
                    <td className="py-3.5 px-3 text-right tabular-nums font-semibold text-[var(--ink)]">
                      {formatPercent(page.like_to_view_ratio)}
                    </td>

                    {/* Views / Follower % */}
                    <td className="py-3.5 px-3 text-right tabular-nums font-semibold text-[var(--ink)]">
                      {formatPercent(page.avg_views_per_follower)}
                    </td>

                    {/* Updated */}
                    <td
                      className={`py-3.5 px-4 text-right tabular-nums whitespace-nowrap text-xs ${
                        page.last_refresh_error ? "text-[var(--cof)] font-semibold" : "text-[var(--mut)]"
                      }`}
                    >
                      {page.last_refresh_error ? "Failed" : formatRelativeTime(page.last_refreshed_at)}
                    </td>

                    {/* Delete Button */}
                    <td className="py-3.5 px-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleDeleteClick(page)}
                        disabled={removeMutation.isPending}
                        aria-label={`Remove @${page.username}`}
                        title="Remove page"
                        className="w-8 h-8 rounded-full border border-[var(--line)] inline-flex items-center justify-center text-[var(--mut)] hover:text-[var(--cof)] hover:border-[var(--cof)] active:scale-95 disabled:opacity-50"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>

                    {/* Refresh Button */}
                    <td className="py-3.5 px-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleRefreshClick(page.id)}
                        disabled={isItemRefreshing}
                        aria-label={`Refresh @${page.username}`}
                        className="w-8 h-8 rounded-full border border-[var(--line)] inline-flex items-center justify-center text-[var(--ink)] hover:border-[var(--cof)] active:scale-95 disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${isItemRefreshing ? "animate-spin text-[var(--cof)]" : ""}`} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {totalResults > 0 && (
        <div className="flex items-center justify-between gap-3 px-1 text-xs text-[var(--mut)]">
          <span>Showing {(page - 1) * 50 + 1}–{Math.min(page * 50, totalResults)} of {totalResults}</span>
          <div className="flex items-center gap-2">
            <button type="button" className="icon-btn" aria-label="Previous page" title="Previous page" disabled={page <= 1} onClick={() => onPageChange(page - 1)}><ChevronLeft className="w-4 h-4" /></button>
            <span>{page} / {Math.max(totalPages, 1)}</span>
            <button type="button" className="icon-btn" aria-label="Next page" title="Next page" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}><ChevronRight className="w-4 h-4" /></button>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!pageToDelete}
        title="Remove page"
        message={pageToDelete ? `Remove @${pageToDelete.username} from your tracked pages?` : ""}
        busy={removeMutation.isPending}
        error={deleteError}
        onConfirm={handleConfirmDelete}
        onCancel={() => setPageToDelete(null)}
      />
    </div>
  );
};
