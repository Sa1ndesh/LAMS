import React from 'react';
import { Card } from './Card';
import { clsx } from 'clsx';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  colorScheme?: 'blue' | 'indigo' | 'emerald' | 'amber' | 'sky' | 'red' | 'purple';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  colorScheme = 'blue',
  onClick,
}) => {
  const colorStyles = {
    blue: 'text-blue-600 bg-blue-50/80 border-blue-100',
    indigo: 'text-indigo-600 bg-indigo-50/80 border-indigo-100',
    emerald: 'text-emerald-600 bg-emerald-50/80 border-emerald-100',
    amber: 'text-amber-600 bg-amber-50/80 border-amber-100',
    sky: 'text-sky-600 bg-sky-50/80 border-sky-100',
    red: 'text-red-600 bg-red-50/80 border-red-100',
    purple: 'text-purple-600 bg-purple-50/80 border-purple-100',
  };

  return (
    <Card
      className={clsx(
        'transition-all duration-200 hover:-translate-y-0.5 cursor-pointer',
        onClick && 'hover:border-lams-secondary/40'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-semibold text-lams-muted uppercase tracking-wider">{title}</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-2xl font-extrabold text-lams-primary tracking-tight">{value}</h3>
            {trend && (
              <span
                className={clsx(
                  'text-xs font-semibold px-1.5 py-0.5 rounded',
                  trend.isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                )}
              >
                {trend.isPositive ? '↑' : '↓'} {trend.value}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-lams-muted">{subtitle}</p>}
        </div>
        <div className={clsx('p-3 rounded-xl border shadow-sm shrink-0', colorStyles[colorScheme])}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Card>
  );
};

