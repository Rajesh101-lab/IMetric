import React, { useEffect, useState } from "react";
import { Plus, Tag, X } from "lucide-react";
import { PageItem } from "@/types";
import { useUpdatePageTags } from "@/hooks/usePages";

const SUGGESTED_TAGS = ["Cricket", "Bollywood edits", "Meme page", "Influencer"];

interface PageTagsEditorProps {
  page: PageItem;
}

export const PageTagsEditor: React.FC<PageTagsEditorProps> = ({ page }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tags, setTags] = useState(page.tags || []);
  const [customTag, setCustomTag] = useState("");
  const [error, setError] = useState<string | null>(null);
  const updateTags = useUpdatePageTags();

  useEffect(() => {
    if (isOpen) setTags(page.tags || []);
  }, [isOpen, page.tags]);

  const toggleTag = (label: string) => {
    const selected = tags.some((tag) => tag.toLowerCase() === label.toLowerCase());
    if (!selected && tags.length >= 12) {
      setError("A page can have up to 12 tags.");
      return;
    }
    setError(null);
    setTags((current) => selected
      ? current.filter((tag) => tag.toLowerCase() !== label.toLowerCase())
      : [...current, label]);
  };

  const addCustomTag = (event: React.FormEvent) => {
    event.preventDefault();
    const label = customTag.trim();
    if (!label) return;
    if (label.length > 32) {
      setError("Tags must be 32 characters or fewer.");
      return;
    }
    if (tags.some((tag) => tag.toLowerCase() === label.toLowerCase())) {
      setCustomTag("");
      return;
    }
    if (tags.length >= 12) {
      setError("A page can have up to 12 tags.");
      return;
    }
    setError(null);
    setTags((current) => [...current, label]);
    setCustomTag("");
  };

  const saveTags = async () => {
    setError(null);
    try {
      await updateTags.mutateAsync({ pageId: page.id, tags });
      setIsOpen(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save page tags.");
    }
  };

  const allOptions = [...new Set([...SUGGESTED_TAGS, ...tags])];

  return (
    <div className="page-tags-editor">
      <div className="page-tag-list">
        {page.tags?.length ? page.tags.map((tag) => <span className="page-tag" key={tag}>{tag}</span>) : (
          <span className="page-tags-empty">No tags</span>
        )}
      </div>
      <button
        type="button"
        className="tag-edit-button"
        onClick={() => setIsOpen(true)}
        aria-label={`Edit tags for @${page.username}`}
        title="Edit page tags"
      >
        <Tag aria-hidden="true" />
      </button>

      {isOpen && (
        <div className="tag-dialog-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setIsOpen(false)}>
          <section className="tag-dialog" role="dialog" aria-modal="true" aria-labelledby={`tag-title-${page.id}`}>
            <header className="tag-dialog-header">
              <div><span className="eyebrow">PAGE TAGS</span><h2 id={`tag-title-${page.id}`}>@{page.username}</h2></div>
              <button type="button" className="icon-btn" aria-label="Close tag editor" onClick={() => setIsOpen(false)}><X /></button>
            </header>
            <p className="tag-dialog-copy">Apply more than one label to this page.</p>
            <div className="tag-options" aria-label="Suggested page tags">
              {allOptions.map((label) => {
                const selected = tags.some((tag) => tag.toLowerCase() === label.toLowerCase());
                return (
                  <button key={label} type="button" className="tag-option" aria-pressed={selected} onClick={() => toggleTag(label)}>
                    <span>{label}</span>{selected && <X aria-hidden="true" />}
                  </button>
                );
              })}
            </div>
            <form className="tag-custom-form" onSubmit={addCustomTag}>
              <input value={customTag} onChange={(event) => setCustomTag(event.target.value)} maxLength={32} placeholder="Add a custom tag" aria-label="Add a custom tag" />
              <button className="icon-btn" type="submit" aria-label="Add custom tag" disabled={!customTag.trim()}><Plus /></button>
            </form>
            {error && <p className="form-error" role="alert">{error}</p>}
            <footer className="tag-dialog-footer">
              <span>{tags.length} / 12 selected</span>
              <div><button type="button" className="app-btn ghost" onClick={() => setIsOpen(false)}>Cancel</button>
                <button type="button" className="app-btn" onClick={saveTags} disabled={updateTags.isPending}>
                  {updateTags.isPending ? "Saving…" : "Save tags"}
                </button></div>
            </footer>
          </section>
        </div>
      )}
    </div>
  );
};