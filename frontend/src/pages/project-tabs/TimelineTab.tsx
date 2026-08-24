import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../hooks/useAuth';
import { TimelineMilestone, Project } from '../../types';
import { workflowApi, WorkflowHistoryResponseData } from '../../services/workflowApi';
import { CheckCircle2, Clock, AlertTriangle, Calendar, Edit, History, User, Check, X, ShieldAlert } from 'lucide-react';

const ALL_STAGES = [
  'Proposal',
  'Verification',
  'Survey',
  'Notification',
  'Award',
  'Compensation',
  'Possession',
  'Rehabilitation & Resettlement',
  'Completed',
];

export const TimelineTab: React.FC = () => {
  const { project } = useOutletContext<{ project: Project }>();
  const { milestones, updateMilestone } = useApp();
  const { canEditProject } = useAuth();

  const [wfData, setWfData] = useState<WorkflowHistoryResponseData | null>(null);
  const [loadingWf, setLoadingWf] = useState(false);

  const [selectedMilestone, setSelectedMilestone] = useState<TimelineMilestone | null>(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [actualDate, setActualDate] = useState('');
  const [mStatus, setMStatus] = useState<TimelineMilestone['status']>('In Progress');

  const fetchHistory = async () => {
    setLoadingWf(true);
    try {
      const res = await workflowApi.getWorkflowHistory(project.id);
      setWfData(res);
    } catch (err) {
      console.warn('Failed to fetch workflow history:', err);
    } finally {
      setLoadingWf(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [project.id]);

  const projectMilestones = milestones.filter((t) => t.projectId === project.id);
  const currentStageIndex = ALL_STAGES.indexOf(project.currentStage);

  const openEditModal = (m: TimelineMilestone) => {
    setSelectedMilestone(m);
    setActualDate(m.actualDate || new Date().toISOString().split('T')[0]);
    setMStatus(m.status);
    setIsEditOpen(true);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMilestone) return;

    updateMilestone(selectedMilestone.id, {
      actualDate,
      status: mStatus,
    });

    setIsEditOpen(false);
    setSelectedMilestone(null);
  };

  return (
    <div className="space-y-6">
      {/* Official 9-Stage Lifecycle Progression */}
      <Card title="National Land Acquisition 9-Stage Lifecycle Flow">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-9 gap-2">
          {ALL_STAGES.map((stg, idx) => {
            const isCompleted = idx < currentStageIndex;
            const isCurrent = idx === currentStageIndex;
            const isPending = idx > currentStageIndex;

            // Find approval info for stage from history
            const histItem = wfData?.history.find((h) => h.new_stage.toLowerCase() === stg.toLowerCase());

            return (
              <div
                key={stg}
                className={`p-3 rounded-xl border text-center transition-all flex flex-col justify-between min-h-[110px] ${
                  isCompleted
                    ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900'
                    : isCurrent
                    ? 'bg-sky-50 border-sky-300 ring-2 ring-sky-400 text-lams-primary shadow-sm font-bold'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}
              >
                <div>
                  <div className="flex items-center justify-center mb-1.5">
                    {isCompleted ? (
                      <span className="h-5 w-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-extrabold">
                        ✓
                      </span>
                    ) : isCurrent ? (
                      <span className="h-5 w-5 rounded-full bg-lams-secondary text-white flex items-center justify-center text-[10px] font-extrabold animate-pulse">
                        →
                      </span>
                    ) : (
                      <span className="h-5 w-5 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center text-[10px] font-semibold">
                        ○
                      </span>
                    )}
                  </div>

                  <div className="text-xs font-bold leading-tight line-clamp-2">{stg}</div>
                </div>

                <div className="mt-2 pt-1 border-t border-slate-200/60 text-[10px]">
                  {isCompleted && histItem ? (
                    <span className="text-emerald-700 font-semibold block truncate">
                      {histItem.user.split(' ')[0]}
                    </span>
                  ) : isCurrent ? (
                    <span className="text-sky-700 font-bold uppercase block tracking-wider text-[9px]">
                      Active
                    </span>
                  ) : (
                    <span className="text-slate-400 block">Pending</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Chronological Workflow History Log */}
      {wfData && wfData.history.length > 0 && (
        <Card title="Official Workflow Audit History Log">
          <div className="space-y-3 text-xs">
            {wfData.history.map((item) => (
              <div
                key={item.id}
                className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-blue-100/70 text-blue-800 rounded-lg shrink-0 mt-0.5">
                    <History className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="font-bold text-slate-800 flex items-center gap-2">
                      <span>Stage Transition: {item.new_stage}</span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                          item.approval_status === 'APPROVED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : item.approval_status === 'REJECTED'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {item.approval_status || 'COMPLETED'}
                      </span>
                    </div>
                    {item.remarks && <p className="text-slate-600 mt-1 italic">"{item.remarks}"</p>}
                  </div>
                </div>

                <div className="text-right text-[11px] text-slate-500 shrink-0">
                  <div className="flex items-center gap-1 justify-end font-semibold text-slate-700">
                    <User className="h-3 w-3 text-slate-400" /> {item.user}
                  </div>
                  <div>{new Date(item.timestamp).toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Milestones Adherence Timeline */}
      <Card title="Project Milestones & Overdue Adherence">
        <div className="relative pl-6 sm:pl-8 space-y-8 before:absolute before:left-3 sm:before:left-4 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
          {projectMilestones.map((item) => {
            const isDone = item.status === 'Completed';
            const isInProgress = item.status === 'In Progress';
            const isDelayed = item.delayDays && item.delayDays > 0;

            return (
              <div key={item.id} className="relative flex items-start group">
                {/* Node */}
                <div
                  className={`absolute -left-6 sm:-left-8 top-0.5 h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ring-4 ring-white ${
                    isDone
                      ? 'bg-emerald-600 text-white'
                      : isInProgress
                      ? 'bg-lams-secondary text-white shadow-md animate-pulse'
                      : 'bg-slate-300 text-slate-600'
                  }`}
                >
                  {isDone ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Clock className="h-3.5 w-3.5" />}
                </div>

                {/* Card */}
                <div className="bg-slate-50 p-4 rounded-xl border border-lams-border w-full flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-lams-primary">{item.title}</span>
                      <StatusBadge status={item.stage} />
                    </div>

                    <div className="flex items-center gap-4 mt-2 text-xs text-lams-muted">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" /> Planned: {item.plannedDate}
                      </span>
                      {item.actualDate && (
                        <span className="font-medium text-slate-800">
                          Actual: {item.actualDate}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {isDelayed && (
                      <span className="flex items-center gap-1 text-xs font-bold text-amber-700 bg-amber-50 px-2 py-1 rounded border border-amber-200">
                        <AlertTriangle className="h-3.5 w-3.5" /> Delayed +{item.delayDays} days
                      </span>
                    )}
                    <StatusBadge status={item.status} />

                    {canEditProject && (
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Edit className="h-3.5 w-3.5 text-lams-secondary" />}
                        onClick={() => openEditModal(item)}
                      />
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Modal: Edit Milestone Completion */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Update Milestone Completion"
        subtitle={selectedMilestone?.title}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleEditSubmit}>
              Save Milestone Progress
            </Button>
          </>
        }
      >
        <form onSubmit={handleEditSubmit} className="space-y-3.5 text-xs">
          <Input
            label="Actual Completion Date *"
            type="date"
            required
            value={actualDate}
            onChange={(e) => setActualDate(e.target.value)}
          />

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Milestone Status *</label>
            <select
              value={mStatus}
              onChange={(e) => setMStatus(e.target.value as TimelineMilestone['status'])}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="In Progress">In Progress</option>
              <option value="Completed">Completed</option>
              <option value="Delayed">Delayed</option>
              <option value="Pending">Pending</option>
            </select>
          </div>
        </form>
      </Modal>
    </div>
  );
};
