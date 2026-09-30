import React from "react";

export const TableSkeleton: React.FC = () => {
  return (
    <div className="w-full space-y-4 animate-pulse p-6">
      <div className="h-8 bg-[var(--line)] rounded-full w-48 mb-6" />
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="h-12 bg-[var(--line)] rounded-2xl w-full" />
      ))}
    </div>
  );
};

export const CardSkeleton: React.FC = () => {
  return (
    <div className="app-card p-6 animate-pulse space-y-4">
      <div className="h-6 bg-[var(--line)] rounded-full w-1/3" />
      <div className="h-10 bg-[var(--line)] rounded-2xl w-full" />
    </div>
  );
};
