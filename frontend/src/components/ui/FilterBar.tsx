import React from 'react';
import { Filter } from 'lucide-react';

export interface FilterOption {
  key: string;
  label: string;
  options: { label: string; value: string }[];
  value: string;
  onChange: (val: string) => void;
}

interface FilterBarProps {
  filters: FilterOption[];
  onReset?: () => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({ filters, onReset }) => {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-lams-muted">
        <Filter className="h-3.5 w-3.5" />
        <span>Filters:</span>
      </div>
      {filters.map((filter) => (
        <select
          key={filter.key}
          value={filter.value}
          onChange={(e) => filter.onChange(e.target.value)}
          className="bg-white border border-lams-border rounded-lg px-3 py-1.5 text-xs font-medium text-lams-dark focus:outline-none focus:ring-1 focus:ring-lams-secondary shadow-sm"
        >
          <option value="ALL">All {filter.label}s</option>
          {filter.options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ))}
      {onReset && (
        <button
          onClick={onReset}
          className="text-xs text-lams-secondary hover:underline font-medium ml-auto"
        >
          Reset Filters
        </button>
      )}
    </div>
  );
};

