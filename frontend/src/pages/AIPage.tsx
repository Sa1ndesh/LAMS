import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { StatCard } from '../components/ui/StatCard';
import { Table, Column } from '../components/ui/Table';
import { aiApi, AIOverviewData, HighRiskProjectData } from '../services/aiApi';
import { Cpu, AlertTriangle, ShieldAlert, CheckCircle2, Sparkles, ArrowRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useNavigate } from 'react-router-dom';

export const AIPage: React.FC = () => {
  const navigate = useNavigate();
  const [overview, setOverview] = useState<AIOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAIOverview = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await aiApi.getAIOverview();
        setOverview(res);
      } catch (err: any) {
        console.warn('Failed to load AI overview:', err);
        setError('Failed to fetch AI decision support overview data.');
      } finally {
        setLoading(false);
      }
    };

    fetchAIOverview();
  }, []);

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-orange-100 text-orange-800">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-800">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">LOW</span>;
    }
  };

  // Recharts Horizontal BarChart Data
  const chartData = overview?.highest_risk_projects.map((p) => ({
    name: p.project_code,
    fullName: p.project_name,
    score: p.risk_score,
  })) || [];

  const columns: Column<HighRiskProjectData>[] = [
    {
      header: 'Project Code & Name',
      cell: (row) => (
        <div>
          <button
            onClick={() => navigate(`/projects/${row.project_id}`)}
            className="font-bold text-xs text-lams-secondary hover:underline text-left block"
          >
            {row.project_name}
          </button>
          <span className="text-[11px] text-lams-muted">{row.project_code} • {row.state}</span>
        </div>
      ),
    },
    {
      header: 'Category & Stage',
      cell: (row) => (
        <div className="text-xs">
          <div className="font-semibold text-lams-dark">{row.category}</div>
          <div className="text-lams-muted text-[11px]">{row.current_stage}</div>
        </div>
      ),
    },
    {
      header: 'Risk Score & Level',
      cell: (row) => (
        <div className="flex items-center gap-2">
          <span className="font-extrabold text-sm text-lams-primary">{row.risk_score}/100</span>
          {getRiskBadge(row.risk_level)}
        </div>
      ),
    },
    {
      header: 'Top Risk Factor',
      cell: (row) => <span className="text-xs text-slate-700 font-medium">{row.top_risk_factor}</span>,
    },
    {
      header: 'Recommended Action',
      cell: (row) => (
        <div className="text-xs text-lams-secondary font-semibold flex items-center gap-1">
          {row.recommended_action} <ArrowRight className="h-3 w-3 shrink-0" />
        </div>
      ),
    },
  ];

  return (
    <PageContainer
      title="AI Decision Support Engine"
      description="Explainable Deterministic Risk Analytics & Bottleneck Intervention Recommendations"
    >
      {/* KPI Cards */}
      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <StatCard
            title="Total Evaluated"
            value={overview.total_projects.toString()}
            subtitle="Active Infrastructure Corridors"
            icon={Cpu}
            colorScheme="blue"
          />
          <StatCard
            title="Low Risk"
            value={overview.low_risk_projects.toString()}
            subtitle="Optimal Schedule"
            icon={CheckCircle2}
            colorScheme="emerald"
          />
          <StatCard
            title="Medium Risk"
            value={overview.medium_risk_projects.toString()}
            subtitle="Minor Operational Slippage"
            icon={ShieldAlert}
            colorScheme="amber"
          />
          <StatCard
            title="High Risk"
            value={overview.high_risk_projects.toString()}
            subtitle="Requires Intervention"
            icon={AlertTriangle}
            colorScheme="indigo"
          />
          <StatCard
            title="Critical Risk"
            value={overview.critical_projects.toString()}
            subtitle="Urgent Escalation"
            icon={AlertTriangle}
            colorScheme="red"
          />
        </div>
      )}

      {/* Grid: Risk Score Chart & National Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Horizontal BarChart */}
        <Card title="Highest Risk Projects (Risk Index Score 0-100)" className="lg:col-span-2">
          <div className="h-72 w-full pt-2">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748B' }} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: '#002046', fontWeight: 600 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#002046', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                  <Bar dataKey="score" name="Risk Score" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.score >= 75 ? '#DC2626' : entry.score >= 50 ? '#EA580C' : entry.score >= 25 ? '#D97706' : '#059669'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-lams-muted">Loading risk scores...</div>
            )}
          </div>
        </Card>

        {/* National Insights Summary */}
        <Card title="National Executive AI Insights">
          <div className="space-y-4 pt-2">
            <div className="p-3 bg-sky-50 rounded-xl border border-sky-100">
              <div className="text-xs text-sky-800 font-bold uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-lams-secondary" /> National Risk Index
              </div>
              <div className="text-2xl font-extrabold text-lams-primary">
                {overview?.average_risk_score} <span className="text-xs font-normal text-lams-muted">/ 100</span>
              </div>
            </div>

            <div className="space-y-2 text-xs text-slate-700">
              {overview?.national_insights.map((insight, idx) => (
                <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 flex items-start gap-2">
                  <span className="font-bold text-lams-secondary shrink-0">•</span>
                  <span>{insight}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* High-Risk Projects Table */}
      <Card title="Highest Priority Action Projects">
        {overview ? (
          <Table data={overview.highest_risk_projects} columns={columns} keyExtractor={(row) => row.project_id} />
        ) : (
          <div className="p-6 text-center text-xs text-lams-muted">Loading high-risk projects list...</div>
        )}
      </Card>
    </PageContainer>
  );
};

