import React from "react";
import { Plus, BarChart3, Settings, Megaphone, ClipboardCheck, Headphones, Sparkles } from "lucide-react";
import { LogoutButton } from "@/components/LogoutButton";
import { Link } from "react-router-dom";

export type NavTab = "metrics" | "add" | "pageMetrics" | "campaigns" | "settings" | "requests";

interface BottomNavProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  isAdmin?: boolean;
  pageCount: number;
  campaignCount: number;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  activeTab,
  onTabChange,
  isAdmin = false,
  pageCount,
  campaignCount,
}) => {
  return (
    <aside className="workspace-sidebar">
      <Link to="/app" className="workspace-brand" aria-label="IMetric agency workspace">
        <span className="workspace-brand-mark">IM</span>
        <span><strong>IMetric</strong><small>Agency workspace</small></span>
      </Link>

      <nav aria-label="Workspace navigation" className="workspace-nav">
        <button
          type="button"
          onClick={() => onTabChange("metrics")}
          aria-current={activeTab === "metrics" ? "page" : undefined}
        >
          <BarChart3 className="w-5 h-5" />
          <span>Overview</span>
        </button>
        <button
          type="button"
          onClick={() => onTabChange("add")}
          aria-current={activeTab === "add" ? "page" : undefined}
        >
          <Plus className="w-5 h-5" />
          <span>Add page</span>
        </button>
        <button
          type="button"
          onClick={() => onTabChange("pageMetrics")}
          aria-current={activeTab === "pageMetrics" ? "page" : undefined}
        >
          <BarChart3 className="w-5 h-5" />
          <span>Page metrics</span>
        </button>
        <button
          type="button"
          onClick={() => onTabChange("campaigns")}
          aria-current={activeTab === "campaigns" ? "page" : undefined}
        >
          <Megaphone className="w-5 h-5" />
          <span>Campaigns</span>
        </button>
        <button
          type="button"
          onClick={() => onTabChange("settings")}
          aria-current={activeTab === "settings" ? "page" : undefined}
        >
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </button>
        {isAdmin && (
          <button
            type="button"
            onClick={() => onTabChange("requests")}
            aria-current={activeTab === "requests" ? "page" : undefined}
          >
            <ClipboardCheck className="w-5 h-5" />
            <span>Requests</span>
          </button>
        )}
      </nav>

      <div className="workspace-sidebar-footer">
        <section className="workspace-sidebar-card">
          <span className="workspace-sidebar-label">Current plan</span>
          <strong>Agency workspace</strong>
          <small>{pageCount.toLocaleString()} pages · {campaignCount} campaigns</small>
        </section>
        <a className="workspace-sidebar-card workspace-support-card" href="mailto:support@pagemetrics.agency">
          <span className="workspace-sidebar-card-icon"><Headphones aria-hidden="true" /></span>
          <span><strong>Help &amp; Support</strong><small>support@pagemetrics.agency</small></span>
          <Sparkles className="workspace-support-spark" aria-hidden="true" />
        </a>
        <LogoutButton />
      </div>
    </aside>
  );
};
