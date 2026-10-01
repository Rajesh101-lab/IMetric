import React, { useState } from "react";
import { TopBar } from "@/components/TopBar";
import { BottomNav, NavTab } from "@/components/BottomNav";
import { AddPageForm } from "@/components/AddPageForm";
import { SettingsSection } from "@/components/SettingsSection";
import { PagesTable } from "@/components/PagesTable";
import { useAuth } from "@/hooks/useAuth";
import { useCampaigns, usePages, useRefreshPage, useRefreshAll } from "@/hooks/usePages";
import { SortField, SortOrder } from "@/types";
import { formatCompactNumber, formatPercent } from "@/lib/format";
import { ArrowRight, Eye, Instagram, Megaphone, Plus, Search, Users, X } from "lucide-react";
import { CampaignsPanel } from "@/components/CampaignsPanel";
import { RegistrationRequestsPanel } from "@/components/RegistrationRequestsPanel";

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>("metrics");
  const [sortField, setSortField] = useState<SortField>("followers");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [searchQuery, setSearchQuery] = useState("");
  const [pageNumber, setPageNumber] = useState(1);
  const [viewMode, setViewMode] = useState<"cards" | "table">("table");
  const [openCampaignId, setOpenCampaignId] = useState<string | null>(null);

  const normalizedSearch = searchQuery.trim().replace(/^@/, "");
  const { data: pages, isLoading, isError, refetch } = usePages(sortField, sortOrder, pageNumber, normalizedSearch);
  const { data: campaigns = [] } = useCampaigns();
  const refreshSingleMutation = useRefreshPage();
  const { startRefreshAll, isRunning: isRefreshingAll, jobStatus } = useRefreshAll();

  const handleSort = (field: SortField, order: SortOrder) => {
    setSortField(field);
    setSortOrder(order);
    setPageNumber(1);
  };

  const handleRefreshSingle = (pageId: string) => {
    refreshSingleMutation.mutate(pageId);
  };

  const handleTabChange = (tab: NavTab) => {
    if (tab === "campaigns") setOpenCampaignId(null);
    setActiveTab(tab);
  };

  const handleOpenCampaign = (campaignId: string) => {
    setOpenCampaignId(campaignId);
    setActiveTab("campaigns");
  };

  const handleRefreshAll = async () => {
    try {
      await startRefreshAll();
    } catch (e) {
      // Handled via state
    }
  };

  const pagesList = pages?.items || [];
  const totalPages = pages?.summary.total_pages || 0;
  const totalFollowers = pages?.summary.total_followers || 0;
  const avgViewsPerFollower = pages?.summary.avg_views_per_follower || 0;

  let progressText: string | null = null;
  if (isRefreshingAll && jobStatus) {
    progressText = `Refreshing ${jobStatus.done + jobStatus.failed}/${jobStatus.total}…`;
  }

  const pageHeading = {
    metrics: { title: "Performance overview", description: "A current read across the Instagram pages your team tracks." },
    pageMetrics: { title: "Page metrics", description: "Review and compare metrics for every tracked Instagram page." },
    campaigns: { title: "Campaigns", description: "Build page collections for launches, partnerships, and content pushes." },
    requests: { title: "Registration requests", description: "Review access requests for your workspace." },
    add: { title: "Add a page", description: "Bring another Instagram account into your workspace." },
    settings: { title: "Workspace settings", description: "Manage your account, appearance, and data preferences." },
  }[activeTab];

  return (
    <div className="workspace-shell">
      <div className="workspace-content">
        <div className="workspace-app-layout">
          <BottomNav
            activeTab={activeTab}
            onTabChange={handleTabChange}
            isAdmin={user?.is_admin}
            pageCount={totalPages}
            campaignCount={campaigns.length}
          />

          <div className="workspace-main-column">
            <TopBar
              username={user?.username}
              onRefreshAll={handleRefreshAll}
              isRefreshing={isRefreshingAll}
              onAccountClick={() => setActiveTab("settings")}
            />
            {activeTab !== "metrics" && (
              <header className="workspace-page-heading">
                <div><span className="workspace-heading-kicker">IMETRIC WORKSPACE</span><h1>{pageHeading.title}</h1><p>{pageHeading.description}</p></div>
              </header>
            )}

            <main className="workspace-main">
              {activeTab === "add" && <AddPageForm />}
              {activeTab === "settings" && <SettingsSection username={user?.username} />}
              {activeTab === "campaigns" && <CampaignsPanel openCampaignId={openCampaignId} onBackToCampaigns={() => setOpenCampaignId(null)} />}
              {activeTab === "requests" && user?.is_admin && <RegistrationRequestsPanel />}

              {activeTab === "pageMetrics" && (
                <section className="dashboard-pages-panel app-card" aria-label="All page metrics">
                  <header className="dashboard-panel-heading">
                    <div><span className="workspace-heading-kicker">TRACKED ACCOUNTS</span><h2>All page metrics</h2><p>Search, sort, refresh, and manage every tracked page.</p></div>
                    <button type="button" className="app-btn ghost dashboard-add-page" onClick={() => setActiveTab("add")}><Plus aria-hidden="true" />Add page</button>
                  </header>
                  <div className="dashboard-search flex items-center gap-2.5 h-11 px-3.5 rounded-md bg-[var(--card)] border border-[var(--line)] text-[var(--mut)] focus-within:border-[var(--cof)] transition-colors">
                    <Search className="w-5 h-5 flex-none text-[var(--mut)]" />
                    <input type="search" value={searchQuery} onChange={(event) => { setSearchQuery(event.target.value); setPageNumber(1); }} placeholder="Search pages or tags" autoComplete="off" className="flex-1 min-w-0 bg-transparent border-0 outline-none text-[var(--ink)] text-sm placeholder-[var(--mut)]" aria-label="Search pages" />
                    {searchQuery && <button type="button" onClick={() => { setSearchQuery(""); setPageNumber(1); }} aria-label="Clear search" className="text-[var(--mut)] hover:text-[var(--ink)] p-1"><X className="w-4 h-4" /></button>}
                  </div>
                  <PagesTable
                    pages={pagesList}
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
                    page={pageNumber}
                    totalPages={pages?.total_pages || 0}
                    totalResults={pages?.total || 0}
                    onPageChange={setPageNumber}
                    hasSearch={Boolean(normalizedSearch)}
                  />
                </section>
              )}

              {activeTab === "metrics" && (
                <div className="dashboard-overview">
                  <section className="overview-metrics" aria-label="Performance summary">
                    <article className="overview-metric app-card">
                      <div className="overview-metric-top"><div><span className="overview-metric-label">Pages tracked</span><span className="overview-metric-state">{totalPages ? "Active" : "Get started"}</span></div><span className="overview-metric-icon"><Instagram aria-hidden="true" /></span></div>
                      <b>{formatCompactNumber(totalPages)}</b><small className="overview-metric-description">Accounts in this workspace.</small>
                    </article>
                    <article className="overview-metric app-card">
                      <div className="overview-metric-top"><div><span className="overview-metric-label">Total followers</span><span className="overview-metric-state">Audience</span></div><span className="overview-metric-icon"><Users aria-hidden="true" /></span></div>
                      <b>{formatCompactNumber(totalFollowers)}</b><small className="overview-metric-description">Combined tracked audience.</small>
                    </article>
                    <article className="overview-metric app-card">
                      <div className="overview-metric-top"><div><span className="overview-metric-label">Avg views / follower</span><span className="overview-metric-state">Recent reels</span></div><span className="overview-metric-icon"><Eye aria-hidden="true" /></span></div>
                      <b>{formatPercent(avgViewsPerFollower)}</b><small className="overview-metric-description">Average across tracked pages.</small>
                    </article>
                    <article className="overview-metric app-card">
                      <div className="overview-metric-top"><div><span className="overview-metric-label">Campaigns</span><span className="overview-metric-state">Collections</span></div><span className="overview-metric-icon"><Megaphone aria-hidden="true" /></span></div>
                      <b>{formatCompactNumber(campaigns.length)}</b><small className="overview-metric-description">Page groups in this workspace.</small>
                    </article>
                  </section>

                  <div className="dashboard-main-grid">
                    <section className="dashboard-pages-panel app-card" aria-label="Page activity">
                      <header className="dashboard-panel-heading">
                        <div><span className="workspace-heading-kicker">TRACKED ACCOUNTS</span><h2>Page metrics</h2><p>Open the full table to compare reach and reel performance.</p></div>
                        <button type="button" className="app-btn ghost dashboard-add-page" onClick={() => setActiveTab("pageMetrics")}><ArrowRight aria-hidden="true" />View table</button>
                      </header>
                    </section>

                    <aside className="dashboard-campaigns-panel" aria-label="Campaign overview">
                      <header className="dashboard-panel-heading">
                        <div><span className="workspace-heading-kicker">PAGE COLLECTIONS</span><h2>Campaigns</h2><p>Pages grouped for active pushes.</p></div>
                        <button type="button" className="icon-btn" aria-label="Open campaigns" title="Open campaigns" onClick={() => setActiveTab("campaigns")}><ArrowRight aria-hidden="true" /></button>
                      </header>
                      {campaigns.length ? (
                        <div className="dashboard-campaign-list">
                          {campaigns.slice(0, 5).map((campaign) => (
                            <button type="button" className="dashboard-campaign-row" key={campaign.id} onClick={() => handleOpenCampaign(campaign.id)}>
                              <span className="dashboard-campaign-icon"><Megaphone aria-hidden="true" /></span>
                              <span className="dashboard-campaign-name"><strong>{campaign.name}</strong><small>{campaign.page_ids.length} tracked {campaign.page_ids.length === 1 ? "page" : "pages"}</small></span>
                              <ArrowRight aria-hidden="true" />
                            </button>
                          ))}
                        </div>
                      ) : (
                        <div className="dashboard-campaign-empty"><Megaphone aria-hidden="true" /><p>No campaigns yet</p><span>Create a collection to organize pages.</span></div>
                      )}
                      <button type="button" className="dashboard-campaign-create" onClick={() => setActiveTab("campaigns")}><Plus aria-hidden="true" />Manage campaigns</button>
                    </aside>
                  </div>
                </div>
              )}
            </main>
          </div>
        </div>
      </div>
    </div>
  );
};
