import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { ProgressBar } from '../../components/ui/ProgressBar';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Project } from '../../types';
import { useAuthContext } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { workflowApi, WorkflowHistoryResponseData, ApprovalItemData } from '../../services/workflowApi';
import { AIRiskPanel } from '../../components/ai/AIRiskPanel';
import { MapPin, Building, Calendar, IndianRupee, Layers, CheckCircle2, Shield, ArrowRight, Clock, AlertTriangle, Check, X, ShieldAlert } from 'lucide-react';

const STAGE_ORDER = [
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

export const OverviewTab: React.FC = () => {
  const { project } = useOutletContext<{ project: Project }>();
  const { role } = useAuthContext();
  const { refreshData, compensationRecords } = useApp();

  const [wfHistory, setWfHistory] = useState<WorkflowHistoryResponseData | null>(null);
  const [loadingWf, setLoadingWf] = useState(false);

  // Transition Modal State
  const [isTransitionOpen, setIsTransitionOpen] = useState(false);
  const [transitionRemarks, setTransitionRemarks] = useState('');
  const [transitionError, setTransitionError] = useState('');
  const [transitioning, setTransitioning] = useState(false);

  // Approval Modal State (Reject Requires Remarks)
  const [rejectModalAppr, setRejectModalAppr] = useState<ApprovalItemData | null>(null);
  const [rejectRemarks, setRejectRemarks] = useState('');
  const [rejectError, setRejectError] = useState('');
  const [rejecting, setRejecting] = useState(false);

  // Success Feedback
  const [actionSuccessMsg, setActionSuccessMsg] = useState('');

  const fetchWorkflow = async () => {
    setLoadingWf(true);
    try {
      const res = await workflowApi.getWorkflowHistory(project.id);
      setWfHistory(res);
    } catch (err) {
      console.warn('Failed to fetch workflow history:', err);
    } finally {
      setLoadingWf(false);
    }
  };

  useEffect(() => {
    if (project?.id) {
      fetchWorkflow();
    }
  }, [project?.id]);

  const currentIdx = STAGE_ORDER.indexOf(project.currentStage);
  const nextStage = currentIdx >= 0 && currentIdx < STAGE_ORDER.length - 1 ? STAGE_ORDER[currentIdx + 1] : null;

  const landProgressPct = project.landProposedHectares > 0 ? Math.round((project.landAcquiredHectares / project.landProposedHectares) * 100) : 0;

  const projCompRecords = compensationRecords.filter((c) => c.projectId === project.id);
  const totalAssessed = projCompRecords.reduce((acc, c) => acc + c.assessedAmountInr, 0);
  const totalDisbursed = projCompRecords.reduce((acc, c) => acc + c.disbursedAmountInr, 0);
  const compProgressPct = totalAssessed > 0 ? Math.round((totalDisbursed / totalAssessed) * 100) : 0;

  const canMutateWorkflow = ['SUPER_ADMIN', 'CENTRAL_MINISTRY', 'STATE_AUTHORITY', 'DISTRICT_ADMIN', 'LAND_ACQUISITION_OFFICER', 'FIELD_OFFICER', 'PROJECT_IMPLEMENTING_AGENCY'].includes(role);
  const canApprove = ['SUPER_ADMIN', 'CENTRAL_MINISTRY', 'STATE_AUTHORITY', 'DISTRICT_ADMIN', 'LAND_ACQUISITION_OFFICER'].includes(role);
  const isViewer = role === 'VIEWER';

  const handleInitiateTransition = async () => {
    if (!nextStage) return;
    setTransitioning(true);
    setTransitionError('');
    try {
      const res = await workflowApi.transitionStage(project.id, nextStage, transitionRemarks);
      setIsTransitionOpen(false);
      setTransitionRemarks('');
      setActionSuccessMsg(`Workflow transition requested: ${res.status === 'APPROVED' ? 'Stage Advanced!' : 'Submitted for Approval.'}`);
      await refreshData();
      await fetchWorkflow();
    } catch (err: any) {
      setTransitionError(err.message || 'Failed to submit stage transition.');
    } finally {
      setTransitioning(false);
    }
  };

  const handleApprove = async (apprId: string) => {
    try {
      await workflowApi.approveWorkflow(project.id, apprId, 'Approved by nodal officer');
      setActionSuccessMsg('Stage transition approved successfully!');
      await refreshData();
      await fetchWorkflow();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleRejectSubmit = async () => {
    if (!rejectModalAppr) return;
    if (!rejectRemarks.trim()) {
      setRejectError('Mandatory: Rejection remarks must be provided.');
      return;
    }
    setRejecting(true);
    setRejectError('');
    try {
      await workflowApi.rejectWorkflow(project.id, rejectModalAppr.id, rejectRemarks);
      setRejectModalAppr(null);
      setRejectRemarks('');
      setActionSuccessMsg('Workflow transition request rejected.');
      await refreshData();
      await fetchWorkflow();
    } catch (err: any) {
      setRejectError(err.message || 'Failed to reject workflow approval.');
    } finally {
      setRejecting(false);
    }
  };

  return (
    <div className="space-[#1261A3] space-y-6">
      {actionSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl font-bold flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" /> {actionSuccessMsg}
          </span>
          <button onClick={() => setActionSuccessMsg('')} className="text-slate-400 hover:text-slate-600">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* 4 Stat Cards Top Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-lams-muted mb-1">
            <span>Land Acquisition</span>
            <MapPin className="h-4 w-4 text-lams-secondary" />
          </div>
          <div className="text-xl font-bold text-lams-dark mb-2">
            {project.landAcquiredHectares} / {project.landProposedHectares} <span className="text-xs font-normal text-lams-muted">Ha</span>
          </div>
          <ProgressBar value={landProgressPct} color="blue" size="sm" />
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-lams-muted mb-1">
            <span>Compensation Treasury</span>
            <IndianRupee className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-xl font-bold text-lams-dark mb-2">
            ₹ {(project.budgetInr / 10000000).toFixed(2)} Cr
          </div>
          <ProgressBar value={compProgressPct} color="emerald" size="sm" label={`${compProgressPct}% Disbursed`} />
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-lams-muted mb-1">
            <span>Current Stage</span>
            <Layers className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="mt-1">
            <StatusBadge status={project.currentStage} />
          </div>
          <div className="text-[11px] text-lams-muted mt-2 font-medium">Stage {currentIdx + 1} of 9</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-lams-muted mb-1">
            <span>Project Health</span>
            <Shield className="h-4 w-4 text-sky-600" />
          </div>
          <div className="mt-1">
            <StatusBadge status={project.status} />
          </div>
          <div className="text-[11px] text-lams-muted mt-2 font-medium">Target: {project.targetCompletionDate}</div>
        </Card>
      </div>

      {/* Embedded Phase 12 AI Decision Support Risk Panel */}
      <AIRiskPanel projectId={project.id} />

      {/* Lifecycle Stage & Transition Control */}
      <Card title="Lifecycle Stage & Transition Control">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
          <div className="flex items-center gap-4">
            <div>
              <div className="text-xs text-lams-muted font-medium">Active Lifecycle Stage</div>
              <div className="text-sm font-extrabold text-lams-primary flex items-center gap-2 mt-0.5">
                {project.currentStage}
              </div>
            </div>

            {nextStage && (
              <>
                <ArrowRight className="h-4 w-4 text-lams-secondary shrink-0" />
                <div>
                  <div className="text-xs text-lams-muted font-medium">Target Next Stage</div>
                  <div className="text-sm font-semibold text-slate-700 mt-0.5">{nextStage}</div>
                </div>
              </>
            )}
          </div>

          <div>
            {canMutateWorkflow && nextStage ? (
              <Button
                variant="primary"
                size="sm"
                icon={<ArrowRight className="h-4 w-4" />}
                onClick={() => setIsTransitionOpen(true)}
                disabled={Boolean(wfHistory?.pending_approval)}
              >
                {wfHistory?.pending_approval ? 'Approval Pending' : `Advance Stage to '${nextStage}'`}
              </Button>
            ) : isViewer ? (
              <span className="text-xs text-slate-500 italic bg-white px-3 py-1.5 rounded-lg border border-slate-200">
                Read-only Workflow Access (Viewer Role)
              </span>
            ) : (
              <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
                Lifecycle Fully Completed
              </span>
            )}
          </div>
        </div>

        {/* Pending Approval Details Card for Authorized Nodal Officers */}
        {wfHistory?.pending_approval && (
          <div className="mt-4 p-4 bg-amber-50/70 border border-amber-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <span>Stage Transition Approval Requested</span>
              </div>
              <span className="text-[11px] text-amber-700">
                Requested on {new Date(wfHistory.pending_approval.requested_at).toLocaleDateString()}
              </span>
            </div>

            <div className="text-xs space-y-1 text-slate-700">
              <div><strong className="text-slate-900">Requested Stage:</strong> {wfHistory.pending_approval.stage}</div>
              <div><strong className="text-slate-900">Requested By:</strong> {wfHistory.pending_approval.requested_by}</div>
              {wfHistory.pending_approval.remarks && (
                <div><strong className="text-slate-900">Remarks:</strong> {wfHistory.pending_approval.remarks}</div>
              )}
            </div>

            {canApprove && (
              <div className="pt-2 border-t border-amber-200 flex items-center gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  icon={<Check className="h-3.5 w-3.5" />}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  onClick={() => handleApprove(wfHistory.pending_approval!.id)}
                >
                  Approve Transition
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<X className="h-3.5 w-3.5" />}
                  className="border-red-300 text-red-700 hover:bg-red-50"
                  onClick={() => setRejectModalAppr(wfHistory.pending_approval!)}
                >
                  Reject Request
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Project Metadata & Administration" className="md:col-span-2 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="text-lams-muted font-medium block">Project Category</span>
              <span className="font-semibold text-lams-dark text-sm flex items-center gap-1.5 mt-1">
                <Layers className="h-4 w-4 text-lams-secondary" /> {project.projectType}
              </span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="text-lams-muted font-medium block">Implementing Agency</span>
              <span className="font-semibold text-lams-dark text-sm flex items-center gap-1.5 mt-1">
                <Building className="h-4 w-4 text-lams-secondary" /> {project.implementingAgency}
              </span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="text-lams-muted font-medium block">Nodal Ministry</span>
              <span className="font-semibold text-lams-dark text-sm flex items-center gap-1.5 mt-1">
                <Shield className="h-4 w-4 text-lams-secondary" /> {project.ministry}
              </span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <span className="text-lams-muted font-medium block">Jurisdiction Location</span>
              <span className="font-semibold text-lams-dark text-sm flex items-center gap-1.5 mt-1">
                <MapPin className="h-4 w-4 text-lams-secondary" /> {project.village}, {project.district}, {project.state}
              </span>
            </div>
          </div>

          <div className="pt-4 border-t border-lams-border">
            <h4 className="font-bold text-xs text-lams-primary mb-2">Scope & Overview Description</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              This national priority infrastructure project encompasses land acquisition across key village administrative units in {project.district}, {project.state}. The project requires a total land footprint of {project.landProposedHectares} hectares for alignment, right-of-way, and safety corridors under the Land Acquisition Act rules.
            </p>
          </div>
        </Card>

        <Card title="Timeline & Governance">
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-lams-border">
              <span className="text-lams-muted font-medium">Notification Date</span>
              <span className="font-semibold text-lams-dark flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-lams-muted" /> {project.startDate}
              </span>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-lams-border">
              <span className="text-lams-muted font-medium">Target Possession Date</span>
              <span className="font-semibold text-lams-dark flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-lams-muted" /> {project.targetCompletionDate}
              </span>
            </div>

            <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
              <div className="flex items-center gap-2 text-emerald-800 font-bold text-xs">
                <CheckCircle2 className="h-4 w-4" /> Gazette 20A Published
              </div>
              <p className="text-[11px] text-emerald-700 mt-1">
                Preliminary notification released. Public hearings completed in {project.village}.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Modal: Transition Stage */}
      <Modal isOpen={isTransitionOpen} title="Advance Lifecycle Stage" onClose={() => setIsTransitionOpen(false)}>
        <div className="space-y-4 text-xs">
          <p className="text-slate-600">
            You are initiating a stage progression from <strong className="text-lams-primary">{project.currentStage}</strong> to <strong className="text-lams-secondary">{nextStage}</strong>.
          </p>

          <Input
            label="Transition Remarks (Optional)"
            placeholder="e.g. Gazette notification 20A verified and published."
            value={transitionRemarks}
            onChange={(e) => setTransitionRemarks(e.target.value)}
          />

          {transitionError && (
            <div className="p-2 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg font-medium">
              {transitionError}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" size="sm" onClick={() => setIsTransitionOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleInitiateTransition} disabled={transitioning}>
              {transitioning ? 'Submitting...' : 'Confirm Stage Transition'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal: Reject Approval */}
      <Modal isOpen={Boolean(rejectModalAppr)} title="Reject Stage Transition Request" onClose={() => setRejectModalAppr(null)}>
        <div className="space-y-4 text-xs">
          <p className="text-slate-600">
            Rejecting request for stage progression to <strong className="text-lams-primary">{rejectModalAppr?.stage}</strong> requested by <strong className="text-slate-800">{rejectModalAppr?.requested_by}</strong>.
          </p>

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">
              Objection Remarks <span className="text-red-600">* Mandatory</span>
            </label>
            <textarea
              rows={3}
              placeholder="State the explicit reasons or missing documentation for rejecting this transition request..."
              value={rejectRemarks}
              onChange={(e) => setRejectRemarks(e.target.value)}
              className="w-full border border-lams-border rounded-lg p-2 text-xs text-lams-dark focus:outline-none focus:ring-1 focus:ring-red-500"
            />
          </div>

          {rejectError && (
            <div className="p-2 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg font-medium">
              {rejectError}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" size="sm" onClick={() => setRejectModalAppr(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              className="bg-red-600 hover:bg-red-700 text-white"
              onClick={handleRejectSubmit}
              disabled={rejecting}
            >
              {rejecting ? 'Rejecting...' : 'Reject Request'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
