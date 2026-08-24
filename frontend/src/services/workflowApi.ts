import { apiClient } from './api';

export interface ApprovalItemData {
  id: string;
  project_id: string;
  stage: string;
  requested_by: string;
  approved_by?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | string;
  remarks?: string;
  requested_at: string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowHistoryItemData {
  id: string;
  project_id: string;
  previous_stage?: string;
  new_stage: string;
  action: string;
  user: string;
  role?: string;
  remarks?: string;
  approval_status?: string;
  timestamp: string;
}

export interface WorkflowHistoryResponseData {
  project_id: string;
  current_stage: string;
  status: string;
  history: WorkflowHistoryItemData[];
  pending_approval?: ApprovalItemData;
}

export interface WorkflowTransitionResponseData {
  message: string;
  status: 'APPROVED' | 'PENDING_APPROVAL' | string;
  approval?: ApprovalItemData;
  project_id: string;
  previous_stage?: string;
  current_stage: string;
}

export const workflowApi = {
  transitionStage: async (
    projectId: string,
    targetStage: string,
    remarks?: string,
    isOverride: boolean = false
  ): Promise<WorkflowTransitionResponseData> => {
    return apiClient<WorkflowTransitionResponseData>(`/projects/${projectId}/workflow/transition`, {
      method: 'POST',
      body: JSON.stringify({ target_stage: targetStage, remarks, is_override: isOverride }),
    });
  },

  approveWorkflow: async (
    projectId: string,
    approvalId: string,
    remarks?: string
  ): Promise<ApprovalItemData> => {
    return apiClient<ApprovalItemData>(`/projects/${projectId}/workflow/approve/${approvalId}`, {
      method: 'POST',
      body: JSON.stringify({ remarks }),
    });
  },

  rejectWorkflow: async (
    projectId: string,
    approvalId: string,
    remarks: string
  ): Promise<ApprovalItemData> => {
    return apiClient<ApprovalItemData>(`/projects/${projectId}/workflow/reject/${approvalId}`, {
      method: 'POST',
      body: JSON.stringify({ remarks }),
    });
  },

  getWorkflowHistory: async (projectId: string): Promise<WorkflowHistoryResponseData> => {
    return apiClient<WorkflowHistoryResponseData>(`/projects/${projectId}/workflow/history`);
  },

  getProjectApprovals: async (projectId: string): Promise<{ items: ApprovalItemData[]; total: number }> => {
    return apiClient<{ items: ApprovalItemData[]; total: number }>(`/projects/${projectId}/workflow/approvals`);
  },
};

