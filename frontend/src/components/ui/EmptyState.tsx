import React from 'react';
import { FolderOpen } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = 'There are currently no items matching your criteria in the system.',
  actionLabel,
  onAction,
  icon,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 sm:p-12 text-center bg-white rounded-xl border border-dashed border-lams-border">
      <div className="p-4 bg-slate-50 text-lams-muted rounded-full mb-3">
        {icon || <FolderOpen className="h-8 w-8 text-lams-secondary" />}
      </div>
      <h4 className="text-base font-bold text-lams-primary">{title}</h4>
      <p className="text-xs text-lams-muted max-w-sm mt-1 mb-4">{description}</p>
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

