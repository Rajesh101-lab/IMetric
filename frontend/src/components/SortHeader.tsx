import React from "react";
import { ChevronUp, ChevronDown, ArrowUpDown } from "lucide-react";
import { SortField, SortOrder } from "@/types";

interface SortHeaderProps {
  field: SortField;
  label: string;
  currentSort: SortField;
  currentOrder: SortOrder;
  onSort: (field: SortField, order: SortOrder) => void;
  align?: "left" | "right";
}

export const SortHeader: React.FC<SortHeaderProps> = ({
  field,
  label,
  currentSort,
  currentOrder,
  onSort,
  align = "right",
}) => {
  const isActive = currentSort === field;

  const handleClick = () => {
    if (isActive) {
      const nextOrder: SortOrder = currentOrder === "asc" ? "desc" : "asc";
      onSort(field, nextOrder);
    } else {
      onSort(field, "desc");
    }
  };

  const ariaSort = isActive ? (currentOrder === "asc" ? "ascending" : "descending") : "none";

  return (
    <th scope="col" aria-sort={ariaSort} className={`py-3.5 px-3 text-${align}`}>
      <button
        type="button"
        onClick={handleClick}
        className={`inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500 rounded px-1.5 py-1 ${
          isActive
            ? "text-[var(--cof)] font-extrabold"
            : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
        } ${align === "right" ? "ml-auto" : ""}`}
      >
        <span>{label}</span>
        {isActive ? (
          currentOrder === "asc" ? (
            <ChevronUp className="w-3.5 h-3.5 text-[var(--cof)]" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-[var(--cof)]" />
          )
        ) : (
          <ArrowUpDown className="w-3 h-3 opacity-40 group-hover:opacity-100" />
        )}
      </button>
    </th>
  );
};
