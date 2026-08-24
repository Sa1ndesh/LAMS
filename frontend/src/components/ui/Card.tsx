import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
  footer?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  headerAction,
  footer,
  className,
  ...props
}) => {
  return (
    <div
      className={twMerge(
        clsx(
          'bg-lams-surface rounded-xl border border-lams-border shadow-card transition-shadow hover:shadow-card-hover overflow-hidden',
          className
        )
      )}
      {...props}
    >
      {(title || headerAction) && (
        <div className="px-6 py-4 border-b border-lams-border flex items-center justify-between gap-4">
          <div>
            {title && <h3 className="text-base font-semibold text-lams-primary">{title}</h3>}
            {subtitle && <p className="text-xs text-lams-muted mt-0.5">{subtitle}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}

      <div className="p-6">{children}</div>

      {footer && (
        <div className="px-6 py-3 bg-gray-50 border-t border-lams-border text-xs text-lams-muted">
          {footer}
        </div>
      )}
    </div>
  );
};

