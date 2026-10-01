import React from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BadgeCheck,
  BriefcaseBusiness,
  Building2,
  Check,
  ChevronDown,
  CirclePlay,
  Database,
  LockKeyhole,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import "./home.css";

const navItems = ["Features", "Pricing", "FAQ"];

const workflowSteps = [
  { step: "01", title: "Add pages", text: "Bring in the pages your team manages and keep them organized by client or campaign." },
  { step: "02", title: "Track metrics", text: "Refresh the key KPIs that matter most to your reporting rhythm and decision making." },
  { step: "03", title: "Share reports", text: "Summarize performance and send a polished snapshot that clients and internal teams can trust." },
];

const featureBlocks = [
  {
    label: "Track every client page",
    title: "One workspace for every page your agency manages.",
    description: "Centralize the pages you care about, review the latest numbers at a glance, and spot change before it becomes a client issue.",
    points: ["Monitor all managed pages in one place", "Track followers, views, and engagement at a glance", "Keep reporting consistent across clients"],
    align: "right",
  },
  {
    label: "Compare performance",
    title: "Spot lift, decline, and outliers without the spreadsheet shuffle.",
    description: "Use median and average views to understand whether a post is an outlier or part of a trend across your portfolio.",
    points: ["See follower growth and view trends together", "Benchmark client pages against each other", "Quickly identify content that is driving reach"],
    align: "left",
  },
];

const useCases = [
  {
    title: "Pages",
    description: "Monitor individual client accounts and track the pages that need attention most.",
    chips: ["Brand pages", "Creator pages", "Affiliate accounts"],
  },
  {
    title: "Campaigns",
    description: "Group pages together for a more strategic view across launches, retainer work, and seasonal content.",
    chips: ["New launches", "Retainer reporting", "Content clusters"],
  },
];

const painPoints = [
  "Manual screenshots across multiple client pages",
  "Scattered spreadsheets and inconsistent updates",
  "No client-ready reports before the check-in",
];

const comparisonRows = [
  ["Unified page tracking", true, false],
  ["Average + median reporting", true, false],
  ["Campaign grouping", true, false],
  ["Client-ready summary views", true, false],
  ["History without manual exports", true, false],
  ["One place to compare performance", true, false],
  ["Low-friction refresh workflow", true, false],
];

const audiences = [
  { title: "Social media agencies", pain: "Keeping client pages in sync without a reporting bottleneck.", benefit: "Faster reporting and cleaner client visibility." },
  { title: "Influencer managers", pain: "Tracking performance across many creator accounts every week.", benefit: "Clearer comparisons and more confident decisions." },
  { title: "In-house brand teams", pain: "Monitoring channel health without fragmenting the data across tools.", benefit: "A single source of truth for performance reviews." },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    summary: "For small teams exploring page tracking.",
    cta: "Start free",
    featured: false,
    features: ["1 workspace", "Basic page tracking", "Weekly email summary"],
  },
  {
    name: "Pro",
    price: "$49",
    summary: "For active teams reporting across multiple pages.",
    cta: "Most popular",
    featured: true,
    features: ["Unlimited pages", "Campaign grouping", "Live metric refreshes", "Shareable reports"],
  },
  {
    name: "Agency",
    price: "$119",
    summary: "For multi-client reporting and larger portfolios.",
    cta: "Talk to sales",
    featured: false,
    features: ["Multi-brand workspaces", "Bulk refresh workflows", "Priority support", "Custom reporting"],
  },
];

const faqs = [
  { q: "Where does the data come from?", a: "IMetric reads public performance data from the relevant social platform sources and keeps the reporting source-aware." },
  { q: "Is it secure and read-only?", a: "Yes. The product is designed for read-only monitoring and keeps access scoped to your team and workspace permissions." },
  { q: "How many pages can I track?", a: "The product supports scaling from a few client pages up to much larger portfolios, with higher tiers optimized for more volume." },
  { q: "Can I export data or share it with clients?", a: "You can use the reporting views and shareable summaries to package the most important results for clients and stakeholders." },
  { q: "Can I cancel anytime?", a: "Yes. Plans are flexible and can be adjusted or canceled without friction according to your team’s needs." },
  { q: "Do you offer support?", a: "Support is available across the paid plans, with a direct path for agency and custom reporting needs." },
];

const sampleRows = [
  { name: "northstarcoffee", followers: "84.2k", views: "31.8k", change: "+12.4%" },
  { name: "cobaltrunning", followers: "126k", views: "46.1k", change: "+8.1%" },
  { name: "studioarchive", followers: "52.7k", views: "18.4k", change: "+5.6%" },
];

const chartBars = [32, 48, 39, 64, 53, 76, 58, 84, 67, 94, 74, 100];

export const Home: React.FC = () => {
  const { user, isLoading } = useAuth();
  const accountHref = user ? "/app" : "/login";
  const accountLabel = isLoading ? "Checking account…" : user ? "My account" : "Sign in";

  return (
    <div className="site-shell">
      <header className="site-nav">
        <Link to="/" className="site-brand" aria-label="IMetric home">
          <span className="site-mark">I<span>M</span></span>
          <span>IMetric</span>
        </Link>

        <nav className="site-nav-links" aria-label="Main navigation">
          {navItems.map((item) => (
            <a key={item} href={item === "Pricing" ? "#pricing" : item === "FAQ" ? "#faq" : "#features"}>{item}</a>
          ))}
        </nav>

        <div className="site-nav-actions">
          <button type="button" className="site-toggle-btn">Theme</button>
          <Link to={accountHref} className="site-nav-cta">
            {accountLabel} <ArrowUpRight aria-hidden="true" />
          </Link>
        </div>
      </header>

      <main>
        <section className="site-hero">
          <div className="site-hero-copy">
            <p className="site-eyebrow"><span /> THE AGENCY SIGNAL DESK</p>
            <h1>
              Your page performance,<br />
              framed for action.
            </h1>
            <p className="site-hero-lede">
              IMetric helps social media teams track all their managed pages in one clean workspace, compare performance with context, and report results without the spreadsheet chaos.
            </p>

            <div className="site-hero-actions">
              <Link to={accountHref} className="site-button site-button-primary">
                {user ? "Open your account" : "Start free"} <ArrowUpRight aria-hidden="true" />
              </Link>
              <a href="#features" className="site-text-link">
                Book a demo <CirclePlay aria-hidden="true" />
              </a>
            </div>

            <div className="site-proofline">
              <ShieldCheck aria-hidden="true" />
              <span>Built for agencies, managers, and in-house teams.</span>
            </div>
          </div>

          <div className="site-preview-wrap" aria-label="Sample IMetric workspace preview">
            <div className="site-preview-note"><span className="site-live-dot" /> SAMPLE WORKSPACE</div>
            <div className="site-preview">
              <div className="site-preview-head">
                <div>
                  <span className="site-preview-kicker">ACCOUNT OVERVIEW</span>
                  <h2>Weekly pulse</h2>
                </div>
                <span className="site-period">LAST 7 DAYS <ArrowDownRight aria-hidden="true" /></span>
              </div>

              <div className="site-preview-stats">
                <div><span>Pages tracked</span><strong>18</strong><small>Across 4 clients</small></div>
                <div><span>Avg. reel views</span><strong>32.6k</strong><small className="site-positive"><ArrowUpRight aria-hidden="true" /> 9.8%</small></div>
              </div>

              <div className="site-chart-block">
                <div className="site-chart-title"><span>Views per post</span><span>Sample trend</span></div>
                <div className="site-chart" aria-hidden="true">
                  {chartBars.map((height, index) => (
                    <span key={index} style={{ height: `${height}%` }} />
                  ))}
                </div>
                <div className="site-chart-labels"><span>MON</span><span>WED</span><span>FRI</span><span>SUN</span></div>
              </div>

              <div className="site-preview-table">
                <div className="site-table-heading"><span>PAGE</span><span>FOLLOWERS</span><span>AVG VIEWS</span><span>CHANGE</span></div>
                {sampleRows.map((row) => (
                  <div className="site-table-row" key={row.name}>
                    <span className="site-account"><span className="site-avatar">{row.name.charAt(0).toUpperCase()}</span>@{row.name}</span>
                    <span>{row.followers}</span>
                    <span>{row.views}</span>
                    <span className="site-positive">{row.change}</span>
                  </div>
                ))}
              </div>
              <p className="site-sample-caption">Illustrative preview · not live account data</p>
            </div>
          </div>
        </section>

        <section className="site-stats-strip">
          <div className="site-stats-inner">
            <div>
              <strong>Unlimited pages</strong>
              <span>Scale across every client account.</span>
            </div>
            <div>
              <strong>Daily refresh</strong>
              <span>Keep the signal current without extra admin.</span>
            </div>
            <div>
              <strong>Client-ready reports</strong>
              <span>Turn raw data into clean snapshots.</span>
            </div>
          </div>
        </section>

        <section className="site-product-section" id="features">
          <div className="site-section-header">
            <p className="site-eyebrow"><span /> PRODUCT WALKTHROUGH</p>
            <h2>From page list to performance story.</h2>
          </div>

          <div className="site-stepper">
            {workflowSteps.map((item) => (
              <article key={item.step} className="site-step-card">
                <span className="site-step-number">{item.step}</span>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="site-feature-band">
          {featureBlocks.map((feature) => (
            <article key={feature.label} className={`site-feature-row ${feature.align === "left" ? "image-left" : "image-right"}`}>
              <div className="site-feature-visual">
                <div className="site-visual-card">
                  <div className="site-mini-header">
                    <span>{feature.label}</span>
                    <span className="site-mini-pill">Live</span>
                  </div>
                  <div className="site-mini-chart">
                    {[38, 48, 60, 52, 74, 88, 78].map((height, chartIndex) => (
                      <span key={chartIndex} style={{ height: `${height}%` }} />
                    ))}
                  </div>
                  <div className="site-mini-metrics">
                    <div>
                      <small>Followers</small>
                      <strong>118k</strong>
                    </div>
                    <div>
                      <small>Avg. views</small>
                      <strong>34k</strong>
                    </div>
                  </div>
                </div>
              </div>

              <div className="site-feature-copy">
                <p className="site-eyebrow"><span /> {feature.label}</p>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
                <ul>
                  {feature.points.map((point) => (
                    <li key={point}><Check aria-hidden="true" /> {point}</li>
                  ))}
                </ul>
              </div>
            </article>
          ))}
        </section>

        <section className="site-use-case-section">
          <div className="site-section-header narrow">
            <p className="site-eyebrow"><span /> TWO WAYS TO USE IT</p>
            <h2>Built to fit the way your team works.</h2>
          </div>

          <div className="site-use-grid">
            {useCases.map((item) => (
              <article key={item.title} className="site-use-card">
                <h3>{item.title}</h3>
                <p>{item.description}</p>
                <div className="site-chip-row">
                  {item.chips.map((chip) => (
                    <span key={chip} className="site-chip">{chip}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="site-workflow-section">
          <div className="site-section-header narrow">
            <p className="site-eyebrow"><span /> HOW IT WORKS</p>
            <h2>Stay clear, consistent, and ready to report.</h2>
          </div>

          <div className="site-steps-grid">
            {workflowSteps.map((item) => (
              <article key={item.step} className="site-flow-card">
                <span>{item.step}</span>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="site-problem-section">
          <div className="site-section-header narrow">
            <p className="site-eyebrow"><span /> THE PROBLEM</p>
            <h2>Manual tracking creates noisy reporting.</h2>
          </div>

          <div className="site-pain-grid">
            {painPoints.map((point, index) => (
              <article key={point} className="site-pain-card">
                <span>{index + 1}</span>
                <p>{point}</p>
              </article>
            ))}
          </div>

          <div className="site-problem-cta">
            <Link to={accountHref} className="site-button site-button-primary">
              {user ? "Open workspace" : "Get started"} <ArrowUpRight aria-hidden="true" />
            </Link>
          </div>
        </section>

        <section className="site-comparison-section">
          <div className="site-section-header narrow">
            <p className="site-eyebrow"><span /> COMPARISON</p>
            <h2>Manual reporting slows teams down.</h2>
          </div>

          <div className="site-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>What you need</th>
                  <th className="highlight">IMetric</th>
                  <th>Manual</th>
                </tr>
              </thead>
              <tbody>
                {comparisonRows.map(([label, metric, manual]) => (
                  <tr key={label as string}>
                    <td>{label as string}</td>
                    <td className="highlight">{metric ? "✓" : "—"}</td>
                    <td>{manual ? "✓" : "✕"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="site-audience-section">
          <div className="site-section-header narrow">
            <p className="site-eyebrow"><span /> WHO IT’S FOR</p>
            <h2>Built for the teams that live in performance updates.</h2>
          </div>

          <div className="site-audience-grid">
            {audiences.map((item) => (
              <article key={item.title} className="site-audience-card">
                <div className="site-audience-icon">
                  {item.title.includes("Agencies") ? <BriefcaseBusiness aria-hidden="true" /> : item.title.includes("Influencer") ? <Users aria-hidden="true" /> : <Building2 aria-hidden="true" />}
                </div>
                <h3>{item.title}</h3>
                <p className="site-audience-pain">{item.pain}</p>
                <p className="site-audience-benefit">{item.benefit}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="site-pricing-section" id="pricing">
          <div className="site-section-header narrow">
            <p className="site-eyebrow"><span /> PRICING</p>
            <h2>Simple plans for growing performance teams.</h2>
          </div>

          <div className="site-pricing-grid">
            {plans.map((plan) => (
              <article key={plan.name} className={`site-price-card ${plan.featured ? "featured" : ""}`}>
                {plan.featured && <span className="site-most-popular">Most popular</span>}
                <h3>{plan.name}</h3>
                <div className="site-price-row">
                  <strong>{plan.price}</strong>
                  <span>/mo</span>
                </div>
                <p>{plan.summary}</p>
                <ul>
                  {plan.features.map((feature) => (
                    <li key={feature}><BadgeCheck aria-hidden="true" /> {feature}</li>
                  ))}
                </ul>
                <Link to={accountHref} className={`site-button ${plan.featured ? "site-button-primary" : "site-button-secondary"}`}>
                  {plan.cta}
                </Link>
              </article>
            ))}
          </div>
        </section>

        <section className="site-faq-section" id="faq">
          <div className="site-section-header narrow">
            <p className="site-eyebrow"><span /> FAQ</p>
            <h2>Questions teams usually ask before switching.</h2>
          </div>

          <div className="site-faq-list">
            {faqs.map((faq, index) => (
              <details key={faq.q} open={index === 0} className="site-faq-item">
                <summary>
                  <span>{faq.q}</span>
                  <ChevronDown aria-hidden="true" />
                </summary>
                <p>{faq.a}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="site-trust-section">
          <div className="site-section-header narrow">
            <p className="site-eyebrow"><span /> TRUST & SAFETY</p>
            <h2>Designed to keep context and access clear.</h2>
          </div>

          <div className="site-trust-grid">
            <article className="site-trust-card">
              <Database aria-hidden="true" />
              <h3>Public data only</h3>
              <p>Focuses on publicly visible performance metrics and page-level reporting.</p>
            </article>
            <article className="site-trust-card">
              <LockKeyhole aria-hidden="true" />
              <h3>Read-only access</h3>
              <p>Built around monitoring and reporting rather than editing public account content.</p>
            </article>
            <article className="site-trust-card">
              <ShieldCheck aria-hidden="true" />
              <h3>Secure by design</h3>
              <p>Permissions and sources are kept transparent to reduce confusion and risk.</p>
            </article>
          </div>
        </section>

        <section className="site-final-cta">
          <div>
            <p className="site-eyebrow"><span /> READY TO MOVE FASTER</p>
            <h2>Turn page tracking into a cleaner reporting rhythm.</h2>
          </div>
          <div className="site-final-cta-actions">
            <Link to={accountHref} className="site-button site-button-light">
              {user ? "Open your account" : "Start free"} <ArrowUpRight aria-hidden="true" />
            </Link>
            <a href="#pricing" className="site-button site-button-ghost">View pricing</a>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <Link to="/" className="site-brand"><span className="site-mark">I<span>M</span></span><span>IMetric</span></Link>
        <div className="site-footer-links">
          <div>
            <h4>Product</h4>
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="#faq">FAQ</a>
          </div>
          <div>
            <h4>Company</h4>
            <a href="#">About</a>
            <a href="#">Customers</a>
            <a href="#">Support</a>
          </div>
          <div>
            <h4>Legal</h4>
            <Link to="/privacy">Privacy</Link>
            <Link to="/terms">Terms</Link>
          </div>
          <div>
            <h4>Resources</h4>
            <a href="#">Blog</a>
            <a href="#">Guides</a>
            <a href="#">Docs</a>
          </div>
        </div>
        <div className="site-footer-meta">
          <span>© {new Date().getFullYear()} IMetric</span>
        </div>
      </footer>
    </div>
  );
};