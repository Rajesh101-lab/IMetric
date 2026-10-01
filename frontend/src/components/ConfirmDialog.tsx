import React from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  busy?: boolean;
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmLabel = "Remove",
  cancelLabel = "Cancel",
  busy = false,
  error,
  onConfirm,
  onCancel,
}) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <button
        type="button"
        className="absolute inset-0 bg-black/40"
        onClick={onCancel}
        aria-label="Close dialog"
        disabled={busy}
      />
      <div className="app-card relative w-full max-w-sm p-5 space-y-4">
        <h2 className="text-lg font-bold text-[var(--ink)]">{title}</h2>
        <p className="text-sm text-[var(--mut)]">{message}</p>
        {error && <p className="text-sm font-semibold text-[var(--cof)]">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" className="app-btn ghost" onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </button>
          <button type="button" className="app-btn" onClick={onConfirm} disabled={busy}>
            {busy ? "Removing…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
