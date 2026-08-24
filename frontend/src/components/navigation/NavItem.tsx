import React from 'react';
import { NavLink } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';
import { clsx } from 'clsx';

interface NavItemProps {
  label: string;
  path: string;
  iconName: string;
  badge?: string | number;
  onClick?: () => void;
}

export const NavItem: React.FC<NavItemProps> = ({
  label,
  path,
  iconName,
  badge,
  onClick,
}) => {
  // Dynamically resolve icon component
  const iconsMap = LucideIcons as unknown as Record<string, React.ElementType>;
  const IconComponent = iconsMap[iconName] || LucideIcons.Folder;

  return (
    <NavLink
      to={path}
      onClick={onClick}
      className={({ isActive }) =>
        clsx(
          'flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors group',
          isActive
            ? 'bg-lams-secondary text-white shadow-sm'
            : 'text-slate-300 hover:bg-white/10 hover:text-white'
        )
      }
    >
      <div className="flex items-center gap-3">
        <IconComponent className="h-5 w-5 shrink-0 transition-transform group-hover:scale-105" />
        <span>{label}</span>
      </div>
      {badge !== undefined && (
        <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-500/30 text-white">
          {badge}
        </span>
      )}
    </NavLink>
  );
};
