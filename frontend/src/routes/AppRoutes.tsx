import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { ProjectLayout } from '../layouts/ProjectLayout';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { Login } from '../pages/Login';
import { Dashboard } from '../pages/Dashboard';

// Lazy-loaded routes for code splitting and bundle size optimization
const ProjectsDirectory = lazy(() => import('../pages/ProjectsDirectory').then(m => ({ default: m.ProjectsDirectory })));
const UserManagement = lazy(() => import('../pages/UserManagement').then(m => ({ default: m.UserManagement })));
const Reports = lazy(() => import('../pages/Reports').then(m => ({ default: m.Reports })));
const AIPage = lazy(() => import('../pages/AIPage').then(m => ({ default: m.AIPage })));

const OverviewTab = lazy(() => import('../pages/project-tabs/OverviewTab').then(m => ({ default: m.OverviewTab })));
const LandParcelsTab = lazy(() => import('../pages/project-tabs/LandParcelsTab').then(m => ({ default: m.LandParcelsTab })));
const NotificationsTab = lazy(() => import('../pages/project-tabs/NotificationsTab').then(m => ({ default: m.NotificationsTab })));
const CompensationTab = lazy(() => import('../pages/project-tabs/CompensationTab').then(m => ({ default: m.CompensationTab })));
const FamiliesTab = lazy(() => import('../pages/project-tabs/FamiliesTab').then(m => ({ default: m.FamiliesTab })));
const DocumentsTab = lazy(() => import('../pages/project-tabs/DocumentsTab').then(m => ({ default: m.DocumentsTab })));
const TimelineTab = lazy(() => import('../pages/project-tabs/TimelineTab').then(m => ({ default: m.TimelineTab })));
const GisMapTab = lazy(() => import('../pages/project-tabs/GisMapTab').then(m => ({ default: m.GisMapTab })));

const PageLoader: React.FC = () => (
  <div className="flex items-center justify-center min-h-[400px] w-full">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lams-blue"></div>
  </div>
);

export const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public Auth Route */}
        <Route path="/login" element={<Login />} />

        {/* Protected Main Portal Shell Layout */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/projects" element={<ProjectsDirectory />} />
            <Route path="/ai" element={<AIPage />} />

            {/* Nested Project Sub-Tab Routes */}
            <Route path="/projects/:id" element={<ProjectLayout />}>
              <Route index element={<OverviewTab />} />
              <Route path="parcels" element={<LandParcelsTab />} />
              <Route path="notifications" element={<NotificationsTab />} />
              <Route path="compensation" element={<CompensationTab />} />
              <Route path="families" element={<FamiliesTab />} />
              <Route path="documents" element={<DocumentsTab />} />
              <Route path="timeline" element={<TimelineTab />} />
              <Route path="map" element={<GisMapTab />} />
            </Route>

            <Route path="/users" element={<UserManagement />} />
            <Route path="/reports" element={<Reports />} />
          </Route>
        </Route>

        {/* Fallback Redirections */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
};
