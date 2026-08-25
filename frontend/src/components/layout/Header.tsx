import React, { useState } from 'react';
import { Menu, Bell, Search, Shield, User as UserIcon, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { useAuthContext } from '../../context/AuthContext';
import { UserRole } from '../../types';

interface HeaderProps {
  onMenuToggle: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
  const navigate = useNavigate();
  const { currentUser, setCurrentUserRole, notifications, markNotificationAsRead, markAllNotificationsAsRead } = useApp();
  const { logout, user: authUser, role, setUserRole } = useAuthContext();
  const [showNotifMenu, setShowNotifMenu] = useState(false);
  const [globalSearch, setGlobalSearch] = useState('');

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (globalSearch.trim()) {
      navigate(`/projects?search=${encodeURIComponent(globalSearch)}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleRoleChange = (newRole: UserRole) => {
    setCurrentUserRole(newRole);
    setUserRole(newRole);
  };

  const handleNotificationClick = (notif: typeof notifications[0]) => {
    markNotificationAsRead(notif.id);
    if (notif.projectId) {
      navigate(`/projects/${notif.projectId}`);
      setShowNotifMenu(false);
    }
  };

  return (
    <header className="bg-lams-primary text-white sticky top-0 z-30 shadow-md border-b border-lams-secondary/30">
      <div className="px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
        {/* Left Section: Mobile Menu & Portal Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuToggle}
            className="lg:hidden p-2 rounded-lg hover:bg-white/10 text-slate-200 focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')}>
            <div className="h-9 w-9 rounded-lg bg-lams-secondary flex items-center justify-center font-bold text-white shadow-inner">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-sky-300">
                  Government of India
                </span>
              </div>
              <h1 className="text-sm sm:text-base font-bold tracking-tight text-white leading-tight">
                National Land Acquisition System
              </h1>
            </div>
          </div>
        </div>

        {/* Center/Right Section: Global Search & User Status */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Quick Search Form */}
          <form onSubmit={handleSearchSubmit} className="hidden md:flex items-center relative w-56 lg:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={globalSearch}
              onChange={(e) => setGlobalSearch(e.target.value)}
              placeholder="Search project, survey #..."
              className="w-full bg-slate-900/60 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-lams-secondary focus:ring-1 focus:ring-lams-secondary"
            />
          </form>

          {/* Notifications Trigger */}
          <div className="relative">
            <button
              onClick={() => setShowNotifMenu(!showNotifMenu)}
              className="relative p-2 rounded-lg hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-amber-400 animate-pulse"></span>
              )}
            </button>

            {/* Notifications Dropdown Panel */}
            {showNotifMenu && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white text-lams-dark rounded-xl shadow-2xl border border-lams-border overflow-hidden z-50">
                <div className="p-3.5 bg-slate-50 border-b border-lams-border flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bell className="h-4 w-4 text-lams-secondary" />
                    <span className="font-bold text-xs text-lams-primary">Notifications</span>
                    {unreadCount > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                        {unreadCount} Unread
                      </span>
                    )}
                  </div>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllNotificationsAsRead}
                      className="text-[11px] text-lams-secondary hover:underline font-semibold"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>

                <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-center text-xs text-lams-muted">No system alerts.</div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        onClick={() => handleNotificationClick(n)}
                        className={`p-3 text-xs cursor-pointer transition-colors ${
                          !n.isRead ? 'bg-blue-50/40 hover:bg-blue-50/80 font-semibold' : 'hover:bg-slate-50 opacity-80'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-bold text-lams-primary">{n.title}</span>
                          <span className="text-[10px] text-lams-muted">{n.date}</span>
                        </div>
                        <p className="text-slate-600 text-[11px] mt-1">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User Profile & Role Selector */}
          <div className="hidden sm:flex items-center gap-2.5 pl-3 border-l border-slate-700">
            <div className="h-8 w-8 rounded-full bg-lams-secondary/80 border border-sky-400/30 flex items-center justify-center text-white font-medium text-xs">
              <UserIcon className="h-4 w-4" />
            </div>
            <div className="text-left">
              <div className="text-xs font-semibold text-white leading-tight">
                {role === 'SUPER_ADMIN' && 'National Super Admin'}
                {role === 'STATE_AUTHORITY' && 'State Land Authority'}
                {role === 'DISTRICT_ADMIN' && 'District Collector (Lucknow)'}
                {role === 'LAND_ACQUISITION_OFFICER' && 'Land Acquisition Officer (LAO)'}
                {role === 'FIELD_OFFICER' && 'Field Survey Officer'}
                {role === 'VIEWER' && 'Public Observer (Read-Only)'}
              </div>
              <select
                value={role}
                onChange={(e) => handleRoleChange(e.target.value as UserRole)}
                className="bg-slate-900 border border-slate-700 rounded px-2 py-0.5 text-[11px] text-sky-300 font-semibold focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer mt-0.5"
              >
                <option value="SUPER_ADMIN">👑 SUPER_ADMIN</option>
                <option value="STATE_AUTHORITY">🏛️ STATE_AUTHORITY</option>
                <option value="DISTRICT_ADMIN">🏢 DISTRICT_ADMIN</option>
                <option value="LAND_ACQUISITION_OFFICER">📜 LAO_OFFICER</option>
                <option value="FIELD_OFFICER">🔍 FIELD_OFFICER</option>
                <option value="VIEWER">👁️ VIEWER</option>
              </select>
            </div>
          </div>

          {/* Sign Out */}
          <button
            onClick={handleLogout}
            className="p-2 rounded-lg hover:bg-red-500/20 text-slate-300 hover:text-red-300 transition-colors"
            title="Sign Out"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
};
