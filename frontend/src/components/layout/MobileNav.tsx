import React from 'react';
import { X, Shield } from 'lucide-react';
import { NavItem } from '../navigation/NavItem';

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const mainNavItems = [
    { label: 'Executive Dashboard', path: '/dashboard', iconName: 'LayoutDashboard' },
    { label: 'Projects Directory', path: '/projects', iconName: 'FolderKanban', badge: 5 },
    { label: 'AI Decision Support', path: '/ai', iconName: 'Cpu' },
    { label: 'User Management', path: '/users', iconName: 'Users' },
    { label: 'Reports & Analytics', path: '/reports', iconName: 'FileText' },
  ];

  return (
    <div className="fixed inset-0 z-50 lg:hidden flex">
      {/* Backdrop overlay */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-4/5 max-w-xs bg-lams-primary text-white flex-1 flex flex-col z-10 shadow-2xl">
        <div className="p-4 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-lams-secondary" />
            <span className="font-bold text-sm text-white">LAMS Menu</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-slate-300"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-4 flex-1 overflow-y-auto">
          <div className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Navigation
          </div>
          <nav className="space-y-1">
            {mainNavItems.map((item) => (
              <NavItem
                key={item.path}
                label={item.label}
                path={item.path}
                iconName={item.iconName}
                badge={item.badge}
                onClick={onClose}
              />
            ))}
          </nav>
        </div>
      </div>
    </div>
  );
};
