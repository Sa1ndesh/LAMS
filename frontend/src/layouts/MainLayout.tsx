import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import { MobileNav } from '../components/layout/MobileNav';

export const MainLayout: React.FC = () => {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-lams-background">
      {/* Top Header */}
      <Header onMenuToggle={() => setMobileNavOpen(!mobileNavOpen)} />

      {/* Main Body Shell */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar */}
        <Sidebar className="hidden lg:flex" />

        {/* Mobile Navigation Drawer */}
        <MobileNav isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto min-w-0">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

