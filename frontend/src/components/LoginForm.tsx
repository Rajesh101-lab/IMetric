import React, { useState } from "react";
import { Eye, EyeOff, Loader2, Lock, Building2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";
import "@/pages/home.css";

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
      navigate("/app");
    } catch (err: any) {
      setLocalError(err.message || "Invalid Agency ID or password.");
    }
  };

  return (
    <div className="site-shell login-shell">
      <header className="site-nav login-nav">
        <Link to="/" className="site-brand" aria-label="IMetric home">
          <span className="site-mark">I<span>M</span></span>
          <span>IMetric</span>
        </Link>
        <ThemeToggle />
      </header>

      <main className="login-main">
        <section className="login-intro">
          <p className="site-eyebrow"><span /> PRIVATE AGENCY WORKSPACE</p>
          <h1>Every client page.<br />One clear view.</h1>
          <p>Sign in to review tracked accounts, compare reel performance, and keep your team’s reporting together.</p>
          <div className="login-points">
            <span><Building2 aria-hidden="true" /> One workspace for managed pages</span>
            <span><Lock aria-hidden="true" /> Access reserved for agency accounts</span>
          </div>
        </section>

        <section className="login-form-panel" aria-labelledby="login-heading">
          <p className="site-eyebrow"><span /> WORKSPACE ACCESS</p>
          <h2 id="login-heading">Sign in</h2>
          <p className="login-form-description">Use your agency credentials to continue.</p>

          {isExpired && !localError && (
            <div className="login-session-message" role="status">
              Your session expired. Sign in again to continue.
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="agency_id" className="block text-xs font-bold uppercase tracking-wider text-[var(--mut)] mb-2">
                Agency ID
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--mut)]">
                  <Building2 className="w-4 h-4" />
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
                  className="login-input pl-10 pr-4"
                />
              </div>
            </div>

            <div>
              <label htmlFor="current-password" className="block text-xs font-bold uppercase tracking-wider text-[var(--mut)] mb-2">
                Password
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--mut)]">
                  <Lock className="w-4 h-4" />
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
                  placeholder="Enter your password"
                  required
                  className="login-input pl-10 pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="login-password-toggle"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div aria-live="polite" className="min-h-[20px]">
              {localError && <p className="text-sm font-semibold text-[var(--cof)]">{localError}</p>}
            </div>

            <button type="submit" disabled={isLoggingIn} className="app-btn w-full justify-center">
              {isLoggingIn ? <><Loader2 className="w-4 h-4 animate-spin" /><span>Signing in…</span></> : <span>Sign in</span>}
            </button>
          </form>
          <p className="login-register-link">
            New to IMetric? <Link to="/register">Create an agency account</Link>
          </p>
        </section>
      </main>

      <footer className="site-footer login-footer">
        <span>IMetric · Agency workspace</span>
        <span className="site-legal-links"><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link></span>
        <Link to="/">Back to website</Link>
      </footer>
    </div>
  );
};
