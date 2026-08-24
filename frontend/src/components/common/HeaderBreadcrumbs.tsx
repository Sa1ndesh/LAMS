import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { Link } from 'react-router-dom';

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export const HeaderBreadcrumbs: React.FC<BreadcrumbsProps> = ({ items }) => {
  return (
    <nav className="flex items-center space-x-2 text-xs text-lams-muted my-2">
      <Link to="/dashboard" className="hover:text-lams-secondary flex items-center gap-1">
        <Home className="h-3.5 w-3.5" />
        <span>Home</span>
      </Link>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
          {item.path ? (
            <Link to={item.path} className="hover:text-lams-secondary font-medium">
              {item.label}
            </Link>
          ) : (
            <span className="font-semibold text-lams-dark">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

