import React from 'react';

interface PageContainerProps {
  title?: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  title,
  description,
  actions,
  children,
}) => {
  return (
    <main className="p-4 sm:p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {(title || actions) && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-lams-border pb-4">
          <div>
            {title && <h1 className="text-xl sm:text-2xl font-bold text-lams-primary tracking-tight">{title}</h1>}
            {description && <p className="text-xs sm:text-sm text-lams-muted mt-1">{description}</p>}
          </div>
          {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
        </div>
      )}
      <div>{children}</div>
    </main>
  );
};

