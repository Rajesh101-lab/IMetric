import React, { useState } from "react";
import { Eye, EyeOff, Loader2, Lock, Building2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";

export const LoginForm: React.FC = () => {
  const [agencyId, setAgencyId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const { login, isLoggingIn } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isExpired = searchParams.get("expired") === "true";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    const cleanId = agencyId.trim();
    if (!cleanId) {
      setLocalError("Please enter your Agency ID.");
      return;
    }
    if (!password) {
      setLocalError("Please enter your password.");
      return;
    }

    try {
      await login({ username: cleanId, password });
      navigate("/");
    } catch (err: any) {
      setLocalError(err.message || "Invalid Agency ID or password.");
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 relative overflow-hidden bg-[var(--bg)] text-[var(--ink)]">
      {/* Absolute top right theme toggle */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md app-card p-8 sm:p-10 relative z-10 my-auto shadow-2xl">
        <div className="text-center mb-8">
          <div className="w-14 h-14 mx-auto mb-4 rounded-3xl bg-[var(--cof)] text-white flex items-center justify-center font-extrabold text-2xl shadow-md">
            M
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-[var(--ink)] tracking-tight">
            Metrics
          </h1>
          <p className="text-sm font-medium text-[var(--mut)] mt-2">
            Sign in to your agency workspace
          </p>
        </div>

        {isExpired && !localError && (
          <div className="mb-6 p-3 rounded-2xl bg-[var(--cofs)] border border-[var(--line)] text-xs font-semibold text-[var(--cof)] text-center">
            Session expired, please sign in again
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Agency ID Input */}
          <div>
            <label htmlFor="agency_id" className="block text-xs font-bold uppercase tracking-wider text-[var(--mut)] mb-2">
              Agency ID
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--mut)]">
                <Building2 className="w-5 h-5" />
              </span>
              <input
                id="agency_id"
                type="text"
                value={agencyId}
                onChange={(e) => {
                  setAgencyId(e.target.value);
                  if (localError) setLocalError(null);
                }}
                disabled={isLoggingIn}
                autoComplete="username"
                placeholder="e.g. acme_media"
                required
                className="w-full pl-11 pr-4 py-3.5 rounded-full bg-[var(--bg)] border border-[var(--line)] text-[var(--ink)] placeholder-[var(--mut)] focus:outline-none focus:border-[var(--cof)] text-base transition-all duration-200 disabled:opacity-60"
              />
            </div>
          </div>

          {/* Password Input */}
          <div>
            <label htmlFor="current-password" className="block text-xs font-bold uppercase tracking-wider text-[var(--mut)] mb-2">
              Password
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--mut)]">
                <Lock className="w-5 h-5" />
              </span>
              <input
                id="current-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (localError) setLocalError(null);
                }}
                disabled={isLoggingIn}
                autoComplete="current-password"
                placeholder="••••••••••••"
                required
                className="w-full pl-11 pr-12 py-3.5 rounded-full bg-[var(--bg)] border border-[var(--line)] text-[var(--ink)] placeholder-[var(--mut)] focus:outline-none focus:border-[var(--cof)] text-base transition-all duration-200 disabled:opacity-60"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--mut)] hover:text-[var(--ink)] transition-colors p-1"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Error display */}
          <div aria-live="polite" className="min-h-[20px]">
            {localError && (
              <p className="text-sm font-semibold text-[var(--cof)] text-center">
                {localError}
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoggingIn}
            className="app-btn w-full justify-center py-4 text-base"
          >
            {isLoggingIn ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Signing in…</span>
              </>
            ) : (
              <span>Sign in</span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
