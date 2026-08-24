import React from 'react';
import { clsx } from 'clsx';

export interface TabItem {
  id: string;
  label: string;
  count?: number | string;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onChange, className = '' }) => {
  return (
    <div className={`border-b border-lams-border overflow-x-auto ${className}`}>
      <nav className="-mb-px flex space-x-6 min-w-max">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={clsx(
                'py-3 px-1 inline-flex items-center gap-2 border-b-2 font-medium text-xs sm:text-sm transition-colors whitespace-nowrap',
                isActive
                  ? 'border-lams-secondary text-lams-secondary font-bold'
                  : 'border-transparent text-lams-muted hover:text-lams-dark hover:border-slate-300'
              )}
            >
              {tab.icon && <span className="shrink-0">{tab.icon}</span>}
              {tab.label}
              {tab.count !== undefined && (
                <span
                  className={clsx(
                    'px-2 py-0.5 rounded-full text-[10px] font-semibold',
                    isActive ? 'bg-blue-100 text-lams-secondary' : 'bg-slate-100 text-slate-600'
                  )}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
};

