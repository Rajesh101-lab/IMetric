import React, { useState } from "react";
import { Loader2, Link2, BarChart2, RefreshCw } from "lucide-react";
import { useAddPage, usePages, useRefreshPage } from "@/hooks/usePages";
import { formatCompactNumber } from "@/lib/format";

export const AddPageForm: React.FC = () => {
  const [inputVal, setInputVal] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [isRetryable, setIsRetryable] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const addPageMutation = useAddPage();

  const { data: pages } = usePages("created_at", "desc");
  const refreshSingleMutation = useRefreshPage();

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLocalError(null);
    setIsRetryable(false);
    setSuccessMsg(null);

    let trimmed = inputVal.trim();
    if (!trimmed) {
      setLocalError("Please enter an Instagram username or URL.");
      return;
    }

    if (trimmed.startsWith("@")) {
      trimmed = trimmed.substring(1).trim();
    }

    const urlPattern = /(?:https?:\/\/)?(?:www\.)?instagram\.com\/([A-Za-z0-9._]{1,30})/i;
    const match = trimmed.match(urlPattern);
    if (match) {
      trimmed = match[1];
    }

    if (!/^[A-Za-z0-9._]{1,30}$/.test(trimmed)) {
      setLocalError("That username isn't valid.");
      return;
    }

    try {
      const page = await addPageMutation.mutateAsync(trimmed);
      setSuccessMsg(`Added @${page.username}. Fetching metrics in the background.`);
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err: any) {
      const msg = err.message || "Something went wrong talking to Instagram. Try again.";
      setLocalError(msg);
      // Determine if error is retryable
      const code = err.code || "";
      const status = err.status || 0;
      if (status === 502 || status === 504 || status === 429 || code === "RATE_LIMIT" || code === "TRANSIENT") {
        setIsRetryable(true);
      }
    }
  };

  const isLoading = addPageMutation.isPending;
  const recentPages = (pages || []).slice(0, 3);

  return (
    <div className="space-y-6 pb-24">
      {/* Primary Hero Card */}
      <div className="app-card p-6 sm:p-8">
        <h2 className="text-2xl font-bold tracking-tight text-[var(--ink)] mb-4">
          Which page are we adding?
        </h2>

        <form onSubmit={handleSubmit}>
          <div className="flex items-center gap-2 border border-[var(--line)] rounded-full h-16 px-3 sm:px-6 bg-[var(--bg)] focus-within:border-[var(--cof)] transition-colors">
            <span className="text-[var(--mut)] text-xl font-medium select-none">
              @
            </span>
            <input
              type="text"
              value={inputVal}
              onChange={(e) => {
                setInputVal(e.target.value);
                if (localError) setLocalError(null);
              }}
              disabled={isLoading}
              placeholder="username or profile link"
              autoComplete="off"
              autoCapitalize="none"
              spellCheck="false"
              className="flex-1 min-w-0 bg-transparent border-0 outline-none text-lg text-[var(--ink)] placeholder-[var(--mut)]"
              aria-label="Instagram username"
            />
            <button
              type="submit"
              disabled={isLoading || !inputVal.trim()}
              className="app-btn h-12 flex-none"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Adding…</span>
                </>
              ) : (
                <span>Add page</span>
              )}
            </button>
          </div>

          <div aria-live="polite" className="mt-3 min-h-[22px] px-2">
            {localError ? (
              <div className="flex items-center justify-between gap-3 text-sm font-semibold text-[var(--cof)] bg-[var(--cofs)] p-2.5 rounded-xl border border-[var(--line)]">
                <span>{localError}</span>
                {isRetryable && (
                  <button
                    type="button"
                    onClick={() => handleSubmit()}
                    className="app-btn h-8 px-4 text-xs font-bold"
                  >
                    Try again
                  </button>
                )}
              </div>
            ) : successMsg ? (
              <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                ✨ {successMsg}
              </p>
            ) : (
              <p className="text-xs text-[var(--mut)]">
                Letters, numbers, dots and underscores.
              </p>
            )}
          </div>
        </form>

        {/* Feature Steps */}
        <div className="mt-6 border-t border-[var(--line)] pt-2 space-y-4">
          <div className="flex items-start gap-3.5 pt-3">
            <Link2 className="w-5 h-5 text-[var(--cof)] flex-none mt-0.5" />
            <div>
              <b className="block font-semibold text-sm text-[var(--ink)]">
                Paste a link or handle
              </b>
              <span className="text-xs text-[var(--mut)]">
                Both instagram.com URLs and @usernames work.
              </span>
            </div>
          </div>

          <div className="flex items-start gap-3.5 pt-3 border-t border-[var(--line)]">
            <BarChart2 className="w-5 h-5 text-[var(--cof)] flex-none mt-0.5" />
            <div>
              <b className="block font-semibold text-sm text-[var(--ink)]">
                Metrics load instantly
              </b>
              <span className="text-xs text-[var(--mut)]">
                Followers, reel views, likes and ratios from the latest 12 reels.
              </span>
            </div>
          </div>

          <div className="flex items-start gap-3.5 pt-3 border-t border-[var(--line)]">
            <RefreshCw className="w-5 h-5 text-[var(--cof)] flex-none mt-0.5" />
            <div>
              <b className="block font-semibold text-sm text-[var(--ink)]">
                Refresh whenever you need
              </b>
              <span className="text-xs text-[var(--mut)]">
                Update one page or all of them from the dashboard.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recently Added Section */}
      <div>
        <div className="mb-3 px-1">
          <h2 className="text-xl font-bold text-[var(--ink)]">
            Recently added
          </h2>
        </div>

        <div className="app-card p-4 sm:p-5 divide-y divide-[var(--line)]">
          {recentPages.length === 0 ? (
            <p className="text-sm text-[var(--mut)] text-center py-6">
              Nothing added yet.
            </p>
          ) : (
            recentPages.map((p) => (
              <div key={p.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                <div className="w-9 h-9 rounded-full bg-[var(--ink)] text-[var(--card)] flex items-center justify-center font-bold text-sm flex-none">
                  {p.username.charAt(0).toUpperCase()}
                </div>
                <b className="font-semibold text-sm text-[var(--ink)] truncate">
                  @{p.username}
                </b>
                <small className="text-xs text-[var(--mut)] ml-auto flex-none font-medium">
                  {formatCompactNumber(p.followers)} followers
                </small>
                <button
                  type="button"
                  onClick={() => refreshSingleMutation.mutate(p.id)}
                  aria-label={`Refresh @${p.username}`}
                  className="w-8 h-8 rounded-full border border-[var(--line)] flex items-center justify-center text-[var(--ink)] hover:border-[var(--cof)] ml-2 transition-all flex-none"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${refreshSingleMutation.isPending && refreshSingleMutation.variables === p.id ? "animate-spin text-[var(--cof)]" : ""}`} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
