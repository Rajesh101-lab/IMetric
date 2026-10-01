import React, { useState } from "react";
import { RefreshCw, AlertCircle, Loader2, Trash2 } from "lucide-react";
import { PageItem } from "@/types";
import { useRemovePage } from "@/hooks/usePages";
import { ConfirmDialog } from "./ConfirmDialog";
import { PageTagsEditor } from "./PageTagsEditor";
import {
  formatCompactNumber,
  formatPercent,
  formatRelativeTime,
  formatNumberWithCommas,
} from "@/lib/format";

interface PageCardProps {
  page: PageItem;
  onRefresh: (id: string) => void;
  isRefreshing: boolean;
}

export const PageCard: React.FC<PageCardProps> = ({ page, onRefresh, isRefreshing }) => {
  const initial = page.username.charAt(0).toUpperCase();
  const removeMutation = useRemovePage();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDelete = () => {
    setDeleteError(null);
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    setDeleteError(null);
    try {
      await removeMutation.mutateAsync(page.id);
      setConfirmOpen(false);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Could not remove this page.");
    }
  };

  if (page.status === "pending") {
    return (
      <article className="app-card p-5 animate-pulse space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-full bg-[var(--line)]" />
          <div className="space-y-1.5 flex-1">
            <div className="h-4 bg-[var(--line)] rounded w-1/2" />
            <div className="h-3 bg-[var(--line)] rounded w-1/3" />
          </div>
        </div>
        <div className="h-12 bg-[var(--line)] rounded-xl w-full flex items-center justify-center text-xs font-semibold text-[var(--mut)]">
          <Loader2 className="w-4 h-4 animate-spin mr-2" />
          Fetching metrics in background…
        </div>
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleDelete}
            disabled={removeMutation.isPending}
            aria-label={`Remove @${page.username}`}
            title="Remove page"
            className="w-9 h-9 rounded-full border border-[var(--line)] flex items-center justify-center text-[var(--mut)] hover:text-[var(--cof)] hover:border-[var(--cof)] transition-all active:scale-95 disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
        <ConfirmDialog
          open={confirmOpen}
          title="Remove page"
          message={`Remove @${page.username} from your tracked pages?`}
          busy={removeMutation.isPending}
          error={deleteError}
          onConfirm={handleConfirmDelete}
          onCancel={() => setConfirmOpen(false)}
        />
      </article>
    );
  }

  const ltvPct = Math.min(100, Math.max(0, page.like_to_view_ratio * 100 * 10));
  const vpfPct = Math.min(100, Math.max(0, page.avg_views_per_follower * 100 * 2));

  return (
    <article className={`app-card p-5 flex flex-col justify-between ${page.status === "failed" ? "border-[var(--cof)]" : ""}`}>
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-full bg-[var(--ink)] text-[var(--card)] flex items-center justify-center font-bold text-lg flex-shrink-0">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-[var(--ink)] text-base leading-snug truncate">
              @{page.username}
            </span>
            {page.source === "backup" && (
              <span
                className="text-[10px] font-bold px-2 py-0.5 rounded-sm bg-[var(--cofs)] text-[var(--cof)] border border-[var(--line)]"
                title={`Meta fetch failed (${page.fallback_reason || "unknown reason"}); this result came from the configured secondary source.`}
              >
                Backup · {page.fallback_reason || "Meta error"}
              </span>
            )}
          </div>
          <div className="text-xs text-[var(--mut)] font-medium">
            Reels sample: {page.reels_sampled}
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="font-bold text-2xl tracking-tight text-[var(--ink)] tabular-nums leading-none" title={formatNumberWithCommas(page.followers)}>
            {formatCompactNumber(page.followers)}
          </div>
          <div className="text-[11px] text-[var(--mut)] font-medium mt-1">
            followers
          </div>
        </div>
      </div>

      <PageTagsEditor page={page} />

      {/* Trio metrics */}
      <div className="grid grid-cols-3 my-4 py-3 border-y border-[var(--line)]">
        <div className="pr-2">
          <span className="block text-[11.5px] text-[var(--mut)]">Avg views</span>
          <b className="text-base font-bold text-[var(--ink)] tabular-nums" title={formatNumberWithCommas(page.avg_views)}>
            {formatCompactNumber(page.avg_views)}
          </b>
        </div>
        <div className="px-2 border-l border-[var(--line)]">
          <span className="block text-[11.5px] text-[var(--mut)]">Median views</span>
          <b className="text-base font-bold text-[var(--ink)] tabular-nums" title={formatNumberWithCommas(page.median_views)}>
            {formatCompactNumber(page.median_views)}
          </b>
        </div>
        <div className="pl-2 border-l border-[var(--line)]">
          <span className="block text-[11.5px] text-[var(--mut)]">Avg likes</span>
          <b className="text-base font-bold text-[var(--ink)] tabular-nums" title={formatNumberWithCommas(page.avg_likes)}>
            {formatCompactNumber(page.avg_likes)}
          </b>
        </div>
      </div>

      {/* Two-column detailed metrics with bars */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div>
          <span className="block text-[11.5px] text-[var(--mut)]">Last reel views</span>
          <b className="text-base font-bold text-[var(--ink)] tabular-nums">
            {page.last_reel_views !== null ? formatCompactNumber(page.last_reel_views) : "—"}
          </b>
        </div>

        <div>
          <span className="block text-[11.5px] text-[var(--mut)]">Last reel likes</span>
          <b className="text-base font-bold text-[var(--ink)] tabular-nums">
            {page.last_reel_likes !== null ? formatCompactNumber(page.last_reel_likes) : "—"}
          </b>
        </div>

        <div>
          <span className="block text-[11.5px] text-[var(--mut)]">Like / view ratio</span>
          <b className="text-sm font-bold text-[var(--ink)] tabular-nums">
            {formatPercent(page.like_to_view_ratio)}
          </b>
          <div className="h-1.5 w-full bg-[var(--line)] rounded-full mt-1.5 overflow-hidden">
            <div
              className="h-full bg-[var(--cof)] rounded-full transition-all duration-300"
              style={{ width: `${ltvPct}%` }}
            />
          </div>
        </div>

        <div>
          <span className="block text-[11.5px] text-[var(--mut)]">Avg views / followers</span>
          <b className="text-sm font-bold text-[var(--ink)] tabular-nums">
            {formatPercent(page.avg_views_per_follower)}
          </b>
          <div className="h-1.5 w-full bg-[var(--line)] rounded-full mt-1.5 overflow-hidden">
            <div
              className="h-full bg-[var(--cof)] rounded-full transition-all duration-300"
              style={{ width: `${vpfPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Error Notice */}
      {(page.status === "failed" || page.last_refresh_error) && (
        <div className="mt-3 text-xs font-semibold text-[var(--cof)] flex items-center justify-between bg-[var(--cofs)] p-2.5 rounded-xl border border-[var(--line)]">
          <div className="flex items-center gap-1.5 pr-2">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{page.error_message || page.last_refresh_error || "Fetch failed."}</span>
          </div>
          <button
            type="button"
            onClick={() => onRefresh(page.id)}
            disabled={isRefreshing}
            className="px-3 py-1 rounded-full bg-[var(--cof)] text-white text-[11px] font-bold flex-none hover:opacity-90 active:scale-95"
          >
            Try again
          </button>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-2 text-xs text-[var(--mut)]">
        <span>
          {page.status === "failed" ? "Failed" : `Updated ${formatRelativeTime(page.last_refreshed_at)}`}
        </span>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleDelete}
            disabled={removeMutation.isPending}
            aria-label={`Remove @${page.username}`}
            title="Remove page"
            className="w-9 h-9 rounded-full border border-[var(--line)] flex items-center justify-center text-[var(--mut)] hover:text-[var(--cof)] hover:border-[var(--cof)] transition-all active:scale-95 disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={() => onRefresh(page.id)}
            disabled={isRefreshing}
            aria-label={`Refresh @${page.username}`}
            title="Refresh metrics"
            className="w-9 h-9 rounded-full border border-[var(--line)] flex items-center justify-center text-[var(--ink)] hover:border-[var(--cof)] transition-all active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-[var(--cof)]" : ""}`} />
          </button>
        </div>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="Remove page"
        message={`Remove @${page.username} from your tracked pages?`}
        busy={removeMutation.isPending}
        error={deleteError}
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmOpen(false)}
      />
    </article>
  );
};
