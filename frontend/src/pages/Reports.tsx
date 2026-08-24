import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatCard } from '../components/ui/StatCard';
import { analyticsApi, AnalyticsSummaryData, StateAnalyticsItemData, LandAnalyticsResponseData, CompensationAnalyticsResponseData, DelayAnalyticsResponseData } from '../services/analyticsApi';
import { FileText, Download, Filter, Search, Calendar, AlertTriangle, CheckCircle2, IndianRupee, MapPin, Layers } from 'lucide-react';
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

export const Reports: React.FC = () => {
  // Global Filters
  const [selectedState, setSelectedState] = useState<number | undefined>(undefined);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [dateError, setDateError] = useState<string>('');

  // Analytics API Data
  const [summary, setSummary] = useState<AnalyticsSummaryData | null>(null);
  const [statesList, setStatesList] = useState<StateAnalyticsItemData[]>([]);
  const [landData, setLandData] = useState<LandAnalyticsResponseData | null>(null);
  const [compData, setCompData] = useState<CompensationAnalyticsResponseData | null>(null);
  const [delayData, setDelayData] = useState<DelayAnalyticsResponseData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalyticsData = async () => {
    if (dateFrom && dateTo && dateFrom > dateTo) {
      setDateError('Date From cannot be later than Date To.');
      return;
    }
    setDateError('');
    setLoading(true);

    try {
      const filters = {
        state_id: selectedState,
        category: selectedCategory || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      };

      const [sumRes, stateRes, landRes, compRes, delayRes] = await Promise.all([
        analyticsApi.getSummary(filters),
        analyticsApi.getStateAnalytics(filters),
        analyticsApi.getLandAnalytics(filters),
        analyticsApi.getCompensationAnalytics(filters),
        analyticsApi.getDelayAnalytics(),
      ]);

      setSummary(sumRes);
      setStatesList(stateRes.items);
      setLandData(landRes);
      setCompData(compRes);
      setDelayResData(delayRes);
    } catch (err: any) {
      console.warn('Failed to load analytics report data:', err);
    } finally {
      setLoading(false);
    }
  };

  const [delayResData, setDelayResData] = useState<DelayAnalyticsResponseData | null>(null);

  useEffect(() => {
    fetchAnalyticsData();
  }, [selectedState, selectedCategory, dateFrom, dateTo]);

  // Recharts Data Formats
  const stateBarData = statesList.map((s) => ({
    name: s.state_name,
    proposed: s.land_proposed_hectares,
    acquired: s.land_acquired_hectares,
  }));

  const compBarData = compData?.by_state.map((c) => ({
    name: c.label,
    assessed: Math.round(c.assessed_amount / 10000000),
    disbursed: Math.round(c.disbursed_amount / 10000000),
  })) || [];

  const delayBarData = delayResData?.by_state.map((d) => ({
    name: d.label,
    delayed: d.count,
  })) || [];

  const reportsList = [
    { id: 'r1', title: 'National Land Acquisition Progress Audit Report', category: 'Land Acquisition Report', format: 'PDF', size: '3.4 MB' },
    { id: 'r2', title: 'State-wise Infrastructure Footprint Ledger', category: 'State-wise Report', format: 'XLSX', size: '5.1 MB' },
    { id: 'r3', title: 'Treasury Compensation Assessment & Disbursement Summary', category: 'Compensation Report', format: 'PDF', size: '2.8 MB' },
    { id: 'r4', title: 'Rehabilitation & Resettlement (R&R) Assistance Ledger', category: 'R&R Report', format: 'XLSX', size: '4.2 MB' },
  ];

  return (
    <PageContainer
      title="National Reports & Analytics Center"
      description="Database Analytics, State Performance Visualizations & Executive Export Audits"
    >
      {/* Global Interactive Filter Bar */}
      <Card className="mb-6">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto text-xs font-semibold">
            <span className="flex items-center gap-1 text-lams-dark">
              <Filter className="h-4 w-4 text-lams-secondary" /> Global Filters:
            </span>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-white border border-lams-border rounded-lg px-2.5 py-1.5 text-xs text-lams-dark focus:outline-none"
            >
              <option value="">All Categories</option>
              <option value="Highway">Highway</option>
              <option value="Railway">Railway</option>
              <option value="Metro">Metro</option>
              <option value="Irrigation">Irrigation</option>
              <option value="Industrial Corridor">Industrial Corridor</option>
              <option value="Renewable Energy">Renewable Energy</option>
            </select>

            {/* Date From */}
            <div className="flex items-center gap-1">
              <span className="text-lams-muted text-[11px]">From:</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-white border border-lams-border rounded-lg px-2 py-1 text-xs text-lams-dark focus:outline-none"
              />
            </div>

            {/* Date To */}
            <div className="flex items-center gap-1">
              <span className="text-lams-muted text-[11px]">To:</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-white border border-lams-border rounded-lg px-2 py-1 text-xs text-lams-dark focus:outline-none"
              />
            </div>

            {(selectedState || selectedCategory || dateFrom || dateTo) && (
              <button
                onClick={() => {
                  setSelectedState(undefined);
                  setSelectedCategory('');
                  setDateFrom('');
                  setDateTo('');
                  setDateError('');
                }}
                className="text-xs text-red-600 hover:underline font-bold"
              >
                Clear Filters
              </button>
            )}
          </div>

          <Button
            variant="outline"
            size="sm"
            icon={<Download className="h-4 w-4" />}
            onClick={() => alert('Exporting Analytics Data Packet (CSV/PDF)...')}
          >
            Export Master Report Data
          </Button>
        </div>

        {dateError && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg font-medium">
            {dateError}
          </div>
        )}
      </Card>

      {/* National KPI Analytics Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Total Land Proposed"
            value={`${summary.total_land_proposed_hectares.toLocaleString()} Ha`}
            subtitle="Acquisition Target"
            icon={MapPin}
            colorScheme="indigo"
          />
          <StatCard
            title="Land Acquired"
            value={`${summary.total_land_acquired_hectares.toLocaleString()} Ha`}
            subtitle={`${summary.acquisition_percentage}% Overall Progress`}
            icon={CheckCircle2}
            colorScheme="emerald"
          />
          <StatCard
            title="Compensation Disbursed"
            value={`₹ ${(summary.total_compensation_disbursed / 10000000).toFixed(2)} Cr`}
            subtitle={`${summary.compensation_percentage}% Treasury Disbursed`}
            icon={IndianRupee}
            colorScheme="amber"
          />
          <StatCard
            title="Delayed / Critical Projects"
            value={`${summary.delayed_projects + summary.critical_projects}`}
            subtitle="Require Executive Clearance"
            icon={AlertTriangle}
            colorScheme="red"
          />
        </div>
      )}

      {/* Recharts Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Chart 1: State-wise Land Footprint */}
        <Card title="1. State-wise Land Footprint (Proposed vs Acquired Hectares)">
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stateBarData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip contentStyle={{ backgroundColor: '#002046', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="proposed" name="Proposed (Ha)" fill="#1261A3" radius={[4, 4, 0, 0]} />
                <Bar dataKey="acquired" name="Acquired (Ha)" fill="#059669" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Chart 2: Compensation Assessed vs Disbursed */}
        <Card title="2. Treasury Compensation Assessment vs Disbursement (₹ Crore)">
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={compBarData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip contentStyle={{ backgroundColor: '#002046', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="assessed" name="Assessed (₹ Cr)" fill="#7C3AED" radius={[4, 4, 0, 0]} />
                <Bar dataKey="disbursed" name="Disbursed (₹ Cr)" fill="#D97706" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Official Audit Documents Grid */}
      <Card title="Official Executive Audit Reports">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reportsList.map((report) => (
            <div key={report.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="p-3 bg-blue-100 text-lams-secondary rounded-xl shrink-0">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-xs text-lams-primary leading-tight">{report.title}</h4>
                  <div className="flex items-center gap-2 mt-1.5 text-[11px] text-lams-muted">
                    <span className="px-2 py-0.5 rounded bg-slate-200 font-semibold text-slate-700">{report.category}</span>
                    <span>• {report.format} ({report.size})</span>
                  </div>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                icon={<Download className="h-3.5 w-3.5" />}
                onClick={() => alert(`Exporting ${report.title}...`)}
              >
                Export
              </Button>
            </div>
          ))}
        </div>
      </Card>
    </PageContainer>
  );
};
