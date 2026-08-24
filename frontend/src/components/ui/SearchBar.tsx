import React from 'react';
import { Search, X } from 'lucide-react';

interface SearchBarProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  className?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  placeholder = 'Search records...',
  className = '',
}) => {
  return (
    <div className={`relative flex items-center ${className}`}>
      <Search className="absolute left-3.5 h-4 w-4 text-lams-muted pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-white border border-lams-border rounded-lg pl-10 pr-9 py-2 text-xs font-medium text-lams-dark placeholder-gray-400 focus:outline-none focus:border-lams-secondary focus:ring-1 focus:ring-lams-secondary shadow-sm transition-colors"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 p-0.5 text-slate-400 hover:text-slate-600 rounded-full"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
};

