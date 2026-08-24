import React from 'react';
import { clsx } from 'clsx';

interface ProgressBarProps {
  value: number; // 0 to 100
  label?: string;
  showPercent?: boolean;
  color?: 'blue' | 'emerald' | 'amber' | 'indigo';
  size?: 'sm' | 'md' | 'lg';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showPercent = true,
  color = 'blue',
  size = 'md',
}) => {
  const percentage = Math.min(100, Math.max(0, value));

  const colors = {
    blue: 'bg-lams-secondary',
    emerald: 'bg-emerald-600',
    amber: 'bg-amber-500',
    indigo: 'bg-indigo-600',
  };

  const heights = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className="w-full space-y-1">
      {(label || showPercent) && (
        <div className="flex justify-between items-center text-xs font-semibold text-lams-dark">
          {label && <span>{label}</span>}
          {showPercent && <span>{percentage}%</span>}
        </div>
      )}
      <div className={`w-full bg-slate-200 rounded-full overflow-hidden ${heights[size]}`}>
        <div
          className={clsx('h-full transition-all duration-500 rounded-full', colors[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

