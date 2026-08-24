import React, { useState, useEffect } from 'react';
import { aiApi, ProjectRiskData, RiskLevel } from '../../services/aiApi';
import { AlertTriangle, CheckCircle2, ShieldAlert, Cpu, Sparkles, ArrowUpRight, Info } from 'lucide-react';

interface AIRiskPanelProps {
  projectId: string;
}

export const AIRiskPanel: React.FC<AIRiskPanelProps> = ({ projectId }) => {
  const [riskData, setRiskData] = useState<ProjectRiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchRiskData = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await aiApi.getProjectRisk(projectId);
        setRiskData(res);
      } catch (err: any) {
        console.warn('Failed to load AI risk panel:', err);
        setError('AI Decision Support Engine analysis currently unavailable.');
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchRiskData();
    }
  }, [projectId]);

  if (loading) {
    return (
      <div className="p-6 bg-white rounded-xl border border-lams-border shadow-sm flex items-center justify-center gap-3 text-xs text-lams-muted">
        <Cpu className="h-5 w-5 animate-pulse text-lams-secondary" />
        Evaluating rule-based decision support indicators...
      </div>
    );
  }

  if (error || !riskData) {
    return (
      <div className="p-6 bg-white rounded-xl border border-lams-border shadow-sm text-xs text-slate-500">
        <div className="flex items-center gap-2 text-amber-600 font-semibold mb-1">
          <Info className="h-4 w-4" /> AI Decision Support
        </div>
        {error || 'No decision support data available for this project.'}
      </div>
    );
  }

  const getRiskColorClass = (level: RiskLevel) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
  };

  const getPriorityBadgeClass = (p: string) => {
    switch (p) {
      case 'URGENT':
        return 'bg-red-100 text-red-800 font-bold';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 font-semibold';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 font-semibold';
      default:
        return 'bg-blue-100 text-blue-800 font-semibold';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-lams-border shadow-sm p-6 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-lams-border pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-sky-50 text-lams-secondary rounded-xl">
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-lams-primary flex items-center gap-2">
              AI Decision Support Engine <span className="text-[10px] bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold">Explainable Model</span>
            </h3>
            <p className="text-xs text-lams-muted">
              Deterministic rule-based risk evaluation based on milestone, land, compensation & R&R indicators
            </p>
          </div>
        </div>

        {/* Risk Score Pill */}
        <div className={`px-4 py-2 rounded-xl border flex items-center gap-3 ${getRiskColorClass(riskData.risk_level)}`}>
          <div>
            <div className="text-[10px] uppercase font-bold tracking-wider opacity-80">Risk Score</div>
            <div className="text-xl font-extrabold">{riskData.risk_score} <span className="text-xs font-normal">/ 100</span></div>
          </div>
          <div className="text-right pl-2 border-l border-current/20">
            <div className="text-[10px] uppercase font-bold tracking-wider opacity-80">Risk Level</div>
            <div className="text-xs font-extrabold uppercase">{riskData.risk_level}</div>
          </div>
        </div>
      </div>

      {/* Confidence Score Bar */}
      <div className="bg-slate-50 p-3 rounded-lg flex items-center justify-between text-xs border border-slate-200">
        <span className="text-slate-600 font-medium flex items-center gap-1.5">
          <ShieldAlert className="h-4 w-4 text-lams-secondary" /> Model Confidence Index:
        </span>
        <span className="font-bold text-lams-dark">
          {Math.round(riskData.confidence * 100)}% <span className="text-[11px] font-normal text-lams-muted">(High Data Completeness)</span>
        </span>
      </div>

      {/* Grid: Risk Factors & Recommended Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Factors */}
        <div>
          <h4 className="font-bold text-xs text-lams-dark uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <AlertTriangle className="h-4 w-4 text-orange-500" /> Detected Risk Factors ({riskData.factors.length})
          </h4>
          {riskData.factors.length > 0 ? (
            <div className="space-y-3">
              {riskData.factors.map((factor, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-lams-primary">{factor.factor}</span>
                    <span className="font-extrabold text-orange-600 text-[11px]">{factor.impact}</span>
                  </div>
                  <p className="text-xs text-slate-600">{factor.description}</p>
                  <div className="text-[11px] text-lams-muted pt-1 flex items-center justify-between">
                    <span>Metric: <strong className="text-slate-700">{factor.current_value}</strong></span>
                    <span>Threshold: {factor.threshold}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 bg-emerald-50 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 shrink-0" /> No negative operational risk factors detected.
            </div>
          )}
        </div>

        {/* Recommended Actions */}
        <div>
          <h4 className="font-bold text-xs text-lams-dark uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Sparkles className="h-4 w-4 text-lams-secondary" /> Actionable Recommendations ({riskData.recommendations.length})
          </h4>
          <div className="space-y-3">
            {riskData.recommendations.map((rec, idx) => (
              <div key={idx} className="p-3 bg-blue-50/50 rounded-lg border border-blue-100 space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-lams-primary flex items-center gap-1">
                    <ArrowUpRight className="h-3.5 w-3.5 text-lams-secondary" /> {rec.title}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] uppercase ${getPriorityBadgeClass(rec.priority)}`}>
                    {rec.priority}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{rec.description}</p>
                <div className="text-[10px] text-lams-muted italic">Target Factor: {rec.related_factor}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

