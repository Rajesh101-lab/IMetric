import React, { useState } from "react";
import { Building2, CheckCircle2, Eye, EyeOff, Lock, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { ThemeToggle } from "@/components/ThemeToggle";
import "@/pages/home.css";

export const RegisterForm: React.FC = () => {
  const [agencyId, setAgencyId] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requestSent, setRequestSent] = useState(false);
  const { register, isRegistering } = useAuth();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      await register({ username: agencyId.trim(), password, contactEmail: contactEmail.trim() });
      setRequestSent(true);
      setPassword("");
      setConfirmPassword("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create your account.");
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
          <p className="site-eyebrow"><span /> YOUR AGENCY WORKSPACE</p>
          <h1>Start with a clearer view.</h1>
          <p>Create an Agency ID to collect the Instagram pages your team tracks and compare their performance in one place.</p>
          <div className="login-points">
            <span><Building2 aria-hidden="true" /> One account for your tracked pages</span>
            <span><Lock aria-hidden="true" /> Passwords are stored securely</span>
          </div>
        </section>

        <section className="login-form-panel" aria-labelledby="register-heading">
          <p className="site-eyebrow"><span /> NEW WORKSPACE</p>
          <h2 id="register-heading">Create your account</h2>
          <p className="login-form-description">Submit your details for workspace-owner approval.</p>

          {requestSent ? (
            <div className="registration-confirmation" role="status">
              <CheckCircle2 aria-hidden="true" />
              <h3>Request sent for review</h3>
              <p><strong>{agencyId.trim().toLowerCase()}</strong> is pending approval. The workspace owner will contact you at <strong>{contactEmail.trim()}</strong>.</p>
              <p>Your chosen password will work only after approval.</p>
              <Link to="/login" className="app-btn ghost">Back to sign in</Link>
            </div>
          ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="new-agency-id" className="block text-xs font-bold uppercase tracking-wider text-[var(--mut)] mb-2">Agency ID</label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--mut)]"><Building2 className="w-4 h-4" /></span>
                <input
                  id="new-agency-id"
                  type="text"
                  value={agencyId}
                  onChange={(event) => setAgencyId(event.target.value)}
                  disabled={isRegistering}
                  autoComplete="username"
                  minLength={1}
                  maxLength={30}
                  pattern="[A-Za-z0-9._]+"
                  title="Use letters, numbers, periods, and underscores."
                  placeholder="e.g. northstar_media"
                  required
                  className="login-input pl-10 pr-4"
                />
              </div>
            </div>

            <div>
              <label htmlFor="contact-email" className="block text-xs font-bold uppercase tracking-wider text-[var(--mut)] mb-2">Contact email</label>
              <input
                id="contact-email"
                type="email"
                value={contactEmail}
                onChange={(event) => setContactEmail(event.target.value)}
                disabled={isRegistering}
                autoComplete="email"
                maxLength={254}
                placeholder="you@agency.com"
                required
                className="login-input px-4"
              />
            </div>

            <div>
              <label htmlFor="new-password" className="block text-xs font-bold uppercase tracking-wider text-[var(--mut)] mb-2">Password</label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--mut)]"><Lock className="w-4 h-4" /></span>
                <input
                  id="new-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  disabled={isRegistering}
                  autoComplete="new-password"
                  minLength={12}
                  maxLength={128}
                  placeholder="At least 12 characters"
                  required
                  className="login-input pl-10 pr-11"
                />
                <button type="button" onClick={() => setShowPassword((visible) => !visible)} aria-label={showPassword ? "Hide password" : "Show password"} className="login-password-toggle">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirm-password" className="block text-xs font-bold uppercase tracking-wider text-[var(--mut)] mb-2">Confirm password</label>
              <input
                id="confirm-password"
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                disabled={isRegistering}
                autoComplete="new-password"
                minLength={12}
                maxLength={128}
                placeholder="Enter it again"
                required
                className="login-input px-4"
              />
            </div>

            <p className="register-password-hint">Use 12+ characters. Avoid your Agency ID and common passwords.</p>
            <div aria-live="polite" className="min-h-[20px]">
              {error && <p className="text-sm font-semibold text-[var(--cof)]" role="alert">{error}</p>}
            </div>
            <button type="submit" disabled={isRegistering} className="app-btn w-full justify-center">
              {isRegistering ? <><Loader2 className="w-4 h-4 animate-spin" /><span>Sending request…</span></> : <span>Request access</span>}
            </button>
          </form>
          )}
          {!requestSent && <p className="login-register-link">Already have an account? <Link to="/login">Sign in</Link></p>}
        </section>
      </main>

      <footer className="site-footer login-footer">
        <span>IMetric · Agency workspace</span>
        <span className="site-legal-links"><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link></span>
        <Link to="/login">Agency sign in</Link>
      </footer>
    </div>
  );
};