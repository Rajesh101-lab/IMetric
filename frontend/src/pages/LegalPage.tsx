import React from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import "./home.css";

type LegalKind = "privacy" | "terms";

const legalContent: Record<LegalKind, { title: string; intro: string; sections: { heading: string; body: string }[] }> = {
  privacy: {
    title: "Privacy policy",
    intro: "Effective October 1, 2026. This policy explains how IMetric handles information used by its public website and authenticated agency workspace.",
    sections: [
      { heading: "Information handled", body: "We process agency account identifiers and authentication/session data to secure workspace access. Tracked-page data can include public follower counts, reel views, likes, and derived engagement ratios for Instagram Business and Creator accounts." },
      { heading: "Data sources", body: "Meta's Instagram Graph API is the primary source. If an administrator enables the backup provider, eligible failed requests may send the requested Instagram username to SerpApi and use its response. The workspace labels which source returned each result." },
      { heading: "How information is used", body: "Information is used to authenticate agency staff, display requested page metrics, and maintain service security. The service does not request direct messages or private posts." },
      { heading: "Security and third parties", body: "Agency passwords are stored as Argon2 hashes. Meta and, when enabled, SerpApi process requests needed to retrieve metrics under their respective terms and privacy policies. Production deployments should use HTTPS/TLS." },
      { heading: "Contact", body: "Questions about this policy can be sent to support@pagemetrics.agency." },
    ],
  },
  terms: {
    title: "Terms of service",
    intro: "Effective October 1, 2026. By using the IMetric website or workspace, you agree to these terms. Do not use the service if you do not agree.",
    sections: [
      { heading: "Service", body: "IMetric provides agency users with tools to track and compare public Instagram Business and Creator page metrics. Meta's Instagram Graph API is the primary data source. An administrator may enable a third-party backup provider for eligible failures." },
      { heading: "Accounts and acceptable use", body: "Agency users are responsible for protecting their account credentials and ensuring they are authorized to track the pages they add. You may not use the service unlawfully or in violation of Meta's Platform Terms or Instagram's Terms of Use." },
      { heading: "Availability and data", body: "The service depends on external providers and may be affected by outages, permissions, rate limits, or API changes. Metrics are provided for informational and reporting purposes and may differ between data sources." },
      { heading: "Changes", body: "These terms may be updated as the service changes. Continued use after an update means you accept the revised terms." },
    ],
  },
};

export const LegalPage: React.FC<{ kind: LegalKind }> = ({ kind }) => {
  const content = legalContent[kind];

  return (
    <div className="site-shell site-legal-page">
      <header className="site-nav">
        <Link to="/" className="site-brand" aria-label="IMetric home">
          <span className="site-mark">I<span>M</span></span>
          <span>IMetric</span>
        </Link>
        <Link to="/app" className="site-nav-cta">Agency sign in</Link>
      </header>
      <main className="site-legal-content">
        <Link to="/" className="site-legal-back"><ArrowLeft aria-hidden="true" /> Back to IMetric</Link>
        <p className="site-eyebrow"><span /> IMETRIC · {kind.toUpperCase()}</p>
        <h1>{content.title}</h1>
        <p className="site-legal-intro">{content.intro}</p>
        {content.sections.map((section) => (
          <section key={section.heading}>
            <h2>{section.heading}</h2>
            <p>{section.body}</p>
          </section>
        ))}
        <footer className="site-legal-footer">
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
        </footer>
      </main>
    </div>
  );
};