import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { StatCard } from '../components/ui/StatCard';
import { Card } from '../components/ui/Card';
import { Table, Column } from '../components/ui/Table';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { useApp } from '../context/AppContext';
import { Project } from '../types';
import { analyticsApi, AnalyticsSummaryData, LandAnalyticsResponseData, WorkflowAnalyticsResponseData } from '../services/analyticsApi';
import {
  FolderKanban,
  MapPin,
  CheckCircle2,
  IndianRupee,
  Users,
  Home,
  AlertTriangle,
  Compass,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useNavigate } from 'react-router-dom';

import { useAuthContext } from '../context/AuthContext';
import { Shield } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { projects } = useApp();
  const { role } = useAuthContext();

  const [summaryData, setSummaryData] = useState<AnalyticsSummaryData | null>(null);
  const [landData, setLandData] = useState<LandAnalyticsResponseData | null>(null);
  const [wfData, setWfData] = useState<WorkflowAnalyticsResponseData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const [sumRes, landRes, wfRes] = await Promise.all([
          analyticsApi.getSummary(),
          analyticsApi.getLandAnalytics(),
          analyticsApi.getWorkflowAnalytics(),
        ]);
        setSummaryData(sumRes);
        setLandData(landRes);
        setWfData(wfRes);
      } catch (err) {
        console.warn('Failed to fetch backend analytics summary:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  // Compute card metrics from backend API or fallback to project state
  const totalProjects = summaryData ? summaryData.total_projects : projects.length;
  const totalProposedHa = summaryData ? summaryData.total_land_proposed_hectares : projects.reduce((acc, p) => acc + p.landProposedHectares, 0);
  const totalAcquiredHa = summaryData ? summaryData.total_land_acquired_hectares : projects.reduce((acc, p) => acc + p.landAcquiredHectares, 0);
  const overallAcquisitionPct = summaryData ? summaryData.acquisition_percentage : (totalProposedHa > 0 ? Math.round((totalAcquiredHa / totalProposedHa) * 100) : 0);

  const totalAssessedInr = summaryData ? summaryData.total_compensation_assessed : 0;
  const totalDisbursedInr = summaryData ? summaryData.total_compensation_disbursed : 0;

  const totalFamilies = summaryData ? summaryData.total_affected_families : 0;
  const displacedFamilies = summaryData ? summaryData.total_displaced_families : 0;
  const delayedProjects = summaryData ? summaryData.delayed_projects + summaryData.critical_projects : projects.filter((p) => p.status === 'DELAYED' || p.status === 'CRITICAL').length;

  const stats = [
    { title: 'Total Projects', value: totalProjects.toString(), subtitle: 'Across Indian States', icon: FolderKanban, color: 'blue' as const },
    { title: 'Land Proposed', value: `${totalProposedHa.toLocaleString('en-IN')} Ha`, subtitle: 'Infrastructure Footprint', icon: MapPin, color: 'indigo' as const },
    { title: 'Land Acquired', value: `${totalAcquiredHa.toLocaleString('en-IN')} Ha`, subtitle: `${overallAcquisitionPct}% Overall Progress`, icon: CheckCircle2, color: 'emerald' as const },
    { title: 'Compensation Assessed', value: `₹ ${(totalAssessedInr / 10000000).toFixed(2)} Cr`, subtitle: 'Collector Evaluated', icon: IndianRupee, color: 'purple' as const },
    { title: 'Compensation Disbursed', value: `₹ ${(totalDisbursedInr / 10000000).toFixed(2)} Cr`, subtitle: 'Direct Beneficiary Transfer', icon: IndianRupee, color: 'amber' as const },
    { title: 'Affected Families', value: totalFamilies.toString(), subtitle: 'Registered in Census', icon: Users, color: 'sky' as const },
    { title: 'Displaced Families', value: displacedFamilies.toString(), subtitle: 'Rehabilitation Allotted', icon: Home, color: 'indigo' as const },
    { title: 'Delayed Projects', value: delayedProjects.toString(), subtitle: 'Requires Inter-Ministerial Review', icon: AlertTriangle, color: 'red' as const },
  ];

  // Dynamic Chart Data from Backend API
  const stateProgressData = landData?.by_state.map((s) => ({
    state: s.label,
    proposed: s.proposed_hectares,
    acquired: s.acquired_hectares,
  })) || [];

  const statusDistributionData = wfData?.stage_distribution.map((d) => ({
    name: d.stage,
    value: d.count,
  })) || [];

  const PIE_COLORS = ['#1261A3', '#0056B3', '#0284C7', '#059669', '#D97706', '#DC2626'];

  const columns: Column<Project>[] = [
    {
      header: 'Project Code & Name',
      cell: (row) => (
        <div>
          <button
            onClick={() => navigate(`/projects/${row.id}`)}
            className="font-bold text-xs text-lams-secondary hover:underline text-left block"
          >
            {row.name}
          </button>
          <span className="text-[11px] text-lams-muted">{row.projectCode} • {row.state}</span>
        </div>
      ),
    },
    {
      header: 'Implementing Agency',
      cell: (row) => (
        <div className="text-xs">
          <div className="font-semibold text-lams-dark">{row.implementingAgency}</div>
          <div className="text-lams-muted text-[11px]">{row.ministry}</div>
        </div>
      ),
    },
    {
      header: 'Land Progress',
      cell: (row) => {
        const pct = row.landProposedHectares > 0 ? Math.round((row.landAcquiredHectares / row.landProposedHectares) * 100) : 0;
        return (
          <div className="w-36 text-xs">
            <ProgressBar value={pct} label={`${row.landAcquiredHectares} / ${row.landProposedHectares} Ha`} color="blue" size="sm" />
          </div>
        );
      },
    },
    {
      header: 'Stage',
      cell: (row) => <StatusBadge status={row.currentStage} />,
    },
    {
      header: 'Health Status',
      cell: (row) => <StatusBadge status={row.status} />,
    },
  ];

  // Filter projects based on active user role perspective
  const filteredProjects = React.useMemo(() => {
    if (role === 'SUPER_ADMIN') return projects;
    if (role === 'STATE_AUTHORITY') return projects.filter(p => p.state === 'Uttar Pradesh' || p.state === 'Tamil Nadu');
    if (role === 'DISTRICT_ADMIN') return projects.filter(p => p.district === 'Lucknow' || p.district === 'Gautam Buddha Nagar');
    if (role === 'LAND_ACQUISITION_OFFICER') return projects.filter(p => p.currentStage === 'Survey' || p.currentStage === 'Notification' || p.currentStage === 'Verification');
    if (role === 'FIELD_OFFICER') return projects.filter(p => p.currentStage === 'Survey' || p.currentStage === 'Possession');
    if (role === 'VIEWER') return projects;
    return projects;
  }, [projects, role]);

  return (
    <PageContainer
      title="National Executive Dashboard"
      description="Central Monitoring Platform for Infrastructure Land Acquisition & Resettlement in India"
    >
      {/* Role Perspective Banner */}
      <div className="bg-slate-900 border border-sky-500/30 rounded-lg p-3 mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-md">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-sky-500/10 rounded-md border border-sky-500/20 text-sky-400">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              Active Role Scope: <span className="text-sky-300 font-mono bg-sky-950 px-2 py-0.5 rounded border border-sky-500/40">{role}</span>
            </div>
            <div className="text-[11px] text-slate-300 mt-0.5">
              {role === 'SUPER_ADMIN' && 'Full National Administrative Access • All 5 Infrastructure Projects across India'}
              {role === 'STATE_AUTHORITY' && 'State Level Oversight • Filtered to Uttar Pradesh & Tamil Nadu State Projects'}
              {role === 'DISTRICT_ADMIN' && 'District Collectorate Oversight • Filtered to Lucknow & Gautam Buddha Nagar Projects'}
              {role === 'LAND_ACQUISITION_OFFICER' && 'Land Acquisition Officer (LAO) • Active Survey, Notification & Award Clearance'}
              {role === 'FIELD_OFFICER' && 'Field Survey Inspector • Ground Survey & Possession Verification Scope'}
              {role === 'VIEWER' && 'Public Read-Only Observer • All Data Mutations & Administrative Action Buttons Disabled'}
            </div>
          </div>
        </div>
        <div className="text-[11px] text-slate-400 bg-slate-850 px-2.5 py-1 rounded border border-slate-700/60 shrink-0 font-mono">
          Showing {filteredProjects.length} of {projects.length} Projects
        </div>
      </div>

      {/* 8 Dynamic Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {stats.map((stat, idx) => (
          <StatCard
            key={idx}
            title={stat.title}
            value={stat.value}
            subtitle={stat.subtitle}
            icon={stat.icon}
            colorScheme={stat.color}
            onClick={() => navigate('/projects')}
          />
        ))}
      </div>

      {/* Dynamic Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Chart 1: State-wise Acquisition Progress */}
        <Card title="State-wise Land Acquisition Progress (Hectares)">
          <div className="h-72 w-full pt-2">
            {stateProgressData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stateProgressData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="state" tick={{ fontSize: 11, fill: '#64748B' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#002046', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Bar dataKey="proposed" name="Land Proposed (Ha)" fill="#1261A3" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="acquired" name="Land Acquired (Ha)" fill="#059669" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-lams-muted">Loading chart data...</div>
            )}
          </div>
        </Card>

        {/* Chart 2: Project Stage Distribution */}
        <Card title="Project Lifecycle Distribution">
          <div className="h-72 w-full flex items-center justify-center">
            {statusDistributionData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusDistributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {statusDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#002046', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-lams-muted">Loading chart data...</div>
            )}
          </div>
        </Card>
      </div>

      {/* GIS Overview Map Banner */}
      <Card className="mb-6 bg-slate-900 text-white border-slate-800 p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sky-400 text-xs font-bold uppercase tracking-wider">
              <Compass className="h-4 w-4" /> National Spatial GIS Layer
            </div>
            <h3 className="text-xl font-bold text-white">Interactive India Land Acquisition Cadastral Grid</h3>
            <p className="text-xs text-slate-300 max-w-2xl">
              Real-time spatial tracking across {projects.length} active infrastructure corridors. Integrated PostGIS geometry visualization.
            </p>
          </div>
          <button
            onClick={() => navigate('/projects/1/map')}
            className="px-5 py-2.5 bg-lams-secondary hover:bg-sky-600 text-white font-semibold text-xs rounded-xl shadow-lg transition-colors shrink-0"
          >
            Launch GIS Map Explorer
          </button>
        </div>
      </Card>

      {/* Priority Projects Table */}
      <Card title={`Role Scope Projects (${filteredProjects.length})`}>
        <Table data={filteredProjects} columns={columns} keyExtractor={(row) => row.id} />
      </Card>
    </PageContainer>
  );
};
