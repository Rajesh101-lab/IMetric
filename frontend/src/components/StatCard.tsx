import React from "react";

interface StatCardProps {
  label: string;
  value: string;
  subtext?: string;
  icon?: React.ReactNode;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, subtext, icon }) => {
  return (
    <div className="glass-card p-5 flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold tracking-wider text-slate-500 dark:text-slate-400 uppercase">
          {label}
        </span>
        {icon && <div className="text-slate-400 dark:text-slate-500">{icon}</div>}
      </div>
      <div>
        <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tabular-nums tracking-tight">
          {value}
        </div>
        {subtext && (
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {subtext}
          </div>
        )}
      </div>
    </div>
  );
};
