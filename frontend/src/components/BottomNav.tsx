import React from "react";
import { Plus, BarChart3, Settings } from "lucide-react";

export type NavTab = "metrics" | "add" | "settings";

interface BottomNavProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, onTabChange }) => {
  return (
    <nav
      aria-label="Main Navigation"
      className="dock-nav"
    >
      {/* 1. Metrics Tab */}
      <button
        type="button"
        onClick={() => onTabChange("metrics")}
        aria-current={activeTab === "metrics" ? "page" : undefined}
        aria-label="Metrics"
      >
        <BarChart3 className="w-5 h-5" />
        {activeTab === "metrics" && <span>Metrics</span>}
      </button>

      {/* 2. Add Page Tab */}
      <button
        type="button"
        onClick={() => onTabChange("add")}
        aria-current={activeTab === "add" ? "page" : undefined}
        aria-label="Add page"
        className="plus-btn"
      >
        <Plus className="w-5 h-5" />
        {activeTab === "add" && <span>Add</span>}
      </button>

      {/* 3. Settings Tab */}
      <button
        type="button"
        onClick={() => onTabChange("settings")}
        aria-current={activeTab === "settings" ? "page" : undefined}
        aria-label="Settings"
      >
        <Settings className="w-5 h-5" />
        {activeTab === "settings" && <span>Settings</span>}
      </button>
    </nav>
  );
};
