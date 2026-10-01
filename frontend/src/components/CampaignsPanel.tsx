import React, { FormEvent, useState } from "react";
import { ArrowLeft, Megaphone, Pencil, Plus, Search, Trash2, Users, X } from "lucide-react";
import { Campaign } from "@/types";
import { useAllPages, useCampaigns, useRemoveCampaign, useSaveCampaign } from "@/hooks/usePages";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { formatCompactNumber } from "@/lib/format";

const emptyCampaign = { name: "", description: "", page_ids: [] as string[] };

interface CampaignsPanelProps {
  openCampaignId: string | null;
  onBackToCampaigns: () => void;
}

export const CampaignsPanel: React.FC<CampaignsPanelProps> = ({ openCampaignId, onBackToCampaigns }) => {
  const { data: campaigns = [], isLoading, isError } = useCampaigns();
  const { data: pages = [], isLoading: pagesLoading, isError: pagesError } = useAllPages();
  const saveCampaign = useSaveCampaign();
  const removeCampaign = useRemoveCampaign();
  const [editing, setEditing] = useState<Campaign | null>(null);
  const [form, setForm] = useState(emptyCampaign);
  const [showForm, setShowForm] = useState(false);
  const [pageSearch, setPageSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Campaign | null>(null);

  const startNew = () => {
    setEditing(null);
    setForm(emptyCampaign);
    setError(null);
    setShowForm(true);
  };

  const startEdit = (campaign: Campaign) => {
    setEditing(campaign);
    setForm({ name: campaign.name, description: campaign.description || "", page_ids: campaign.page_ids });
    setError(null);
    setShowForm(true);
  };

  const togglePage = (pageId: string) => {
    setForm((current) => ({
      ...current,
      page_ids: current.page_ids.includes(pageId)
        ? current.page_ids.filter((id) => id !== pageId)
        : [...current.page_ids, pageId],
    }));
  };

  const handleSave = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await saveCampaign.mutateAsync({ ...form, name: form.name.trim(), description: form.description.trim(), id: editing?.id });
      setShowForm(false);
      setEditing(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save this campaign.");
    }
  };

  const handleDelete = async () => {
    if (!pendingDelete) return;
    setDeleteError(null);
    try {
      await removeCampaign.mutateAsync(pendingDelete.id);
      setPendingDelete(null);
    } catch (caught) {
      setDeleteError(caught instanceof Error ? caught.message : "Could not delete this campaign.");
    }
  };

  const matchingPages = pages.filter((page) => {
    const query = pageSearch.trim().toLowerCase().replace(/^@/, "");
    return !query || page.username.toLowerCase().includes(query) || page.tags.some((tag) => tag.toLowerCase().includes(query));
  });
  const visiblePages = matchingPages.slice(0, 100);
  const selectedCampaign = campaigns.find((campaign) => campaign.id === openCampaignId) || null;
  const selectedCampaignPages = selectedCampaign
    ? pages.filter((page) => selectedCampaign.page_ids.includes(page.id))
    : [];
  const selectedAudience = selectedCampaignPages.reduce((sum, page) => sum + page.followers, 0);

  return (
    <section className="campaigns-workspace" aria-label="Campaign management">
      <div className="campaigns-toolbar">
        <div><span className="eyebrow">PAGE COLLECTIONS</span><h2>{selectedCampaign ? selectedCampaign.name : <>Your campaigns <span>{campaigns.length}</span></>}</h2></div>
        {selectedCampaign ? (
          <div className="campaign-detail-actions">
            <button type="button" className="app-btn ghost" onClick={onBackToCampaigns}><ArrowLeft aria-hidden="true" />All campaigns</button>
            <button type="button" className="app-btn" onClick={() => startEdit(selectedCampaign)}><Pencil aria-hidden="true" />Edit campaign</button>
          </div>
        ) : <button type="button" className="app-btn" onClick={startNew}><Plus aria-hidden="true" />New campaign</button>}
      </div>

      {isError && <div className="inline-error" role="alert">Could not load campaigns. Try refreshing the page.</div>}
      {selectedCampaign ? (
        <section className="campaign-detail-panel app-card">
          <header><div><span className="eyebrow">CAMPAIGN SUMMARY</span><p>{selectedCampaign.description || "No description added."}</p></div><div><strong>{selectedCampaign.page_ids.length}</strong><small>pages</small></div><div><strong>{formatCompactNumber(selectedAudience)}</strong><small>combined followers</small></div></header>
          <h3>Selected pages</h3>
          {pagesLoading ? <p className="campaign-detail-empty">Loading page details…</p> : selectedCampaignPages.length ? (
            <div className="campaign-detail-pages">
              {selectedCampaignPages.map((page) => (
                <div className="campaign-detail-page" key={page.id}>
                  <span className="campaign-page-avatar">{page.username.slice(0, 1).toUpperCase()}</span>
                  <span className="campaign-page-details"><strong>@{page.username}</strong><small>{formatCompactNumber(page.followers)} followers · {formatCompactNumber(page.avg_views)} avg views</small></span>
                  <span className="campaign-page-tags">{page.tags.length ? page.tags.join(" · ") : "Untagged"}</span>
                </div>
              ))}
            </div>
          ) : <p className="campaign-detail-empty">This campaign has no pages assigned.</p>}
        </section>
      ) : isLoading ? <div className="campaign-empty">Loading campaigns…</div> : campaigns.length === 0 ? (
        <div className="campaign-empty"><Megaphone aria-hidden="true" /><h3>No campaigns yet</h3><p>Create a collection of pages for your next push.</p></div>
      ) : (
        <div className="campaign-list">
          {campaigns.map((campaign) => {
            const campaignPages = pages.filter((page) => campaign.page_ids.includes(page.id));
            const audience = campaignPages.reduce((sum, page) => sum + page.followers, 0);
            return (
              <article className="campaign-row" key={campaign.id}>
                <span className="campaign-mark"><Megaphone aria-hidden="true" /></span>
                <div className="campaign-description"><h3>{campaign.name}</h3><p>{campaign.description || "No description"}</p>
                  <div className="campaign-page-names">{campaignPages.slice(0, 5).map((page) => <span key={page.id}>@{page.username}</span>)}{campaignPages.length > 5 && <span>+{campaignPages.length - 5} more</span>}
                    {campaignPages.length === 0 && <span>No pages assigned</span>}
                  </div>
                </div>
                <div className="campaign-stat"><Users aria-hidden="true" /><strong>{campaign.page_ids.length}</strong><span>pages</span></div>
                <div className="campaign-stat campaign-audience"><strong>{formatCompactNumber(audience)}</strong><span>combined followers</span></div>
                <div className="campaign-actions">
                  <button type="button" className="icon-btn" title="Edit campaign" aria-label={`Edit ${campaign.name}`} onClick={() => startEdit(campaign)}><Pencil /></button>
                  <button type="button" className="icon-btn" title="Delete campaign" aria-label={`Delete ${campaign.name}`} onClick={() => { setDeleteError(null); setPendingDelete(campaign); }}><Trash2 /></button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {showForm && (
        <div className="tag-dialog-backdrop">
          <section className="campaign-dialog" role="dialog" aria-modal="true" aria-labelledby="campaign-form-title">
            <header className="tag-dialog-header">
              <div><span className="eyebrow">CAMPAIGN SETUP</span><h2 id="campaign-form-title">{editing ? "Edit campaign" : "New campaign"}</h2></div>
              <button type="button" className="icon-btn" aria-label="Close campaign form" onClick={() => setShowForm(false)}><X /></button>
            </header>
            <form onSubmit={handleSave}>
              <label className="field-label">Campaign name<input autoFocus required maxLength={80} value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="e.g. Diwali creator launch" /></label>
              <label className="field-label">Description <span>Optional</span><textarea maxLength={255} rows={2} value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} placeholder="What is this campaign about?" /></label>
              <div className="campaign-picker-heading"><div><strong>Choose pages</strong><span>Pick from all {pages.length} tracked pages</span></div><b>{form.page_ids.length} selected</b></div>
              <label className="campaign-page-search"><Search aria-hidden="true" /><input value={pageSearch} onChange={(event) => setPageSearch(event.target.value)} placeholder="Search username or tag" aria-label="Search campaign pages" /></label>
              <div className="campaign-page-picker">
                {pagesLoading ? <p>Loading tracked pages…</p> : pagesError ? <p>Could not load pages for campaign selection.</p> : visiblePages.length ? visiblePages.map((page) => (
                  <label className="campaign-page-choice" key={page.id}>
                    <input type="checkbox" checked={form.page_ids.includes(page.id)} onChange={() => togglePage(page.id)} />
                    <span className="campaign-page-avatar">{page.username.slice(0, 1).toUpperCase()}</span>
                    <span className="campaign-page-details"><strong>@{page.username}</strong><small>{formatCompactNumber(page.followers)} followers</small></span>
                    {page.tags?.length > 0 && <span className="campaign-page-tags">{page.tags.slice(0, 2).join(" · ")}</span>}
                  </label>
                )) : <p>{pages.length ? "No pages match your search." : "Add pages to your workspace before building a campaign."}</p>}
              </div>
              {!pagesLoading && matchingPages.length > visiblePages.length && <p className="campaign-picker-limit">Showing first {visiblePages.length} matches. Refine your search to narrow the list.</p>}
              {error && <p className="form-error" role="alert">{error}</p>}
              <footer className="tag-dialog-footer">
                <span>{form.page_ids.length} pages included</span>
                <div><button type="button" className="app-btn ghost" onClick={() => setShowForm(false)}>Cancel</button>
                  <button type="submit" className="app-btn" disabled={saveCampaign.isPending || !form.name.trim()}>{saveCampaign.isPending ? "Saving…" : editing ? "Save changes" : "Create campaign"}</button></div>
              </footer>
            </form>
          </section>
        </div>
      )}

      <ConfirmDialog
        open={!!pendingDelete}
        title="Delete campaign"
        message={pendingDelete ? `Delete ${pendingDelete.name}? Its tracked pages will remain in your workspace.` : ""}
        busy={removeCampaign.isPending}
        error={deleteError}
        onConfirm={handleDelete}
        onCancel={() => { setDeleteError(null); setPendingDelete(null); }}
      />
    </section>
  );
};