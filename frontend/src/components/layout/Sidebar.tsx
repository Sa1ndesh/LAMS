import React from 'react';
import { NavItem } from '../navigation/NavItem';

interface SidebarProps {
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const mainNavItems = [
    { label: 'Executive Dashboard', path: '/dashboard', iconName: 'LayoutDashboard' },
    { label: 'Projects Directory', path: '/projects', iconName: 'FolderKanban', badge: 5 },
    { label: 'AI Decision Support', path: '/ai', iconName: 'Cpu' },
    { label: 'User Management', path: '/users', iconName: 'Users' },
    { label: 'Reports & Analytics', path: '/reports', iconName: 'FileText' },
  ];

  return (
    <aside className={`w-64 bg-lams-primary border-r border-slate-800 shrink-0 flex flex-col ${className || ''}`}>
      <div className="p-4 flex-1 flex flex-col justify-between overflow-y-auto">
        <div>
          <div className="px-3 mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Core Portal Modules
          </div>
          <nav className="space-y-1">
            {mainNavItems.map((item) => (
              <NavItem
                key={item.path}
                label={item.label}
                path={item.path}
                iconName={item.iconName}
                badge={item.badge}
              />
            ))}
          </nav>
        </div>

        {/* System Version Footer */}
        <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400 px-3">
          <div className="font-semibold text-slate-300">LAMS v1.0.0 (Phase 12)</div>
          <div>National Portal • Ministry of Land Resources</div>
        </div>
      </div>
    </aside>
  );
};
