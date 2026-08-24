import { apiClient } from './api';

export interface AnalyticsFilterParams {
  state_id?: number;
  district_id?: number;
  project_id?: string;
  category?: string;
  status?: string;
  current_stage?: string;
  date_from?: string;
  date_to?: string;
}

export interface AnalyticsSummaryData {
  total_projects: number;
  total_land_proposed_hectares: number;
  total_land_acquired_hectares: number;
  acquisition_percentage: number;
  total_compensation_assessed: number;
  total_compensation_approved: number;
  total_compensation_disbursed: number;
  compensation_percentage: number;
  total_affected_families: number;
  total_displaced_families: number;
  total_resettled_families: number;
  delayed_projects: number;
  critical_projects: number;
  completed_projects: number;
}

export interface StateAnalyticsItemData {
  state_id: number;
  state_name: string;
  project_count: number;
  land_proposed_hectares: number;
  land_acquired_hectares: number;
  acquisition_percentage: number;
  compensation_assessed: number;
  compensation_disbursed: number;
  compensation_percentage: number;
  affected_families: number;
  displaced_families: number;
  delayed_projects: number;
  completed_projects: number;
}

export interface ProjectAnalyticsItemData {
  project_id: string;
  project_code: string;
  project_name: string;
  state: string;
  district: string;
  category: string;
  project_status: string;
  current_stage: string;
  land_proposed: number;
  land_acquired: number;
  acquisition_percentage: number;
  compensation_assessed: number;
  compensation_disbursed: number;
  compensation_percentage: number;
  affected_families: number;
  displaced_families: number;
  delay_days: number;
  risk_indicator: string;
}

export interface LandAnalyticsGroupData {
  group_by: string;
  label: string;
  proposed_hectares: number;
  acquired_hectares: number;
  pending_hectares: number;
  acquisition_percentage: number;
}

export interface LandAnalyticsResponseData {
  total_proposed: number;
  total_acquired: number;
  total_pending: number;
  overall_percentage: number;
  by_state: LandAnalyticsGroupData[];
  by_project: LandAnalyticsGroupData[];
  by_land_type: LandAnalyticsGroupData[];
  by_status: LandAnalyticsGroupData[];
}

export interface CompensationAnalyticsGroupData {
  group_by: string;
  label: string;
  assessed_amount: number;
  approved_amount: number;
  disbursed_amount: number;
  pending_amount: number;
  disbursement_percentage: number;
}

export interface CompensationAnalyticsResponseData {
  total_assessed: number;
  total_approved: number;
  total_disbursed: number;
  total_pending: number;
  overall_percentage: number;
  by_project: CompensationAnalyticsGroupData[];
  by_state: CompensationAnalyticsGroupData[];
  by_payment_status: CompensationAnalyticsGroupData[];
}

export interface WorkflowAnalyticsResponseData {
  stage_distribution: Array<{ stage: string; count: number }>;
  pending_approvals: number;
  approved_approvals: number;
  rejected_approvals: number;
  total_approvals: number;
}

export interface DelayAnalyticsResponseData {
  delayed_projects_count: number;
  critical_projects_count: number;
  total_delayed_milestones: number;
  average_project_delay_days: number;
  max_project_delay_days: number;
  by_state: Array<{ label: string; count: number }>;
  by_category: Array<{ label: string; count: number }>;
  by_stage: Array<{ label: string; count: number }>;
}

const buildQueryString = (params: AnalyticsFilterParams = {}): string => {
  const q = new URLSearchParams();
  if (params.state_id) q.append('state_id', params.state_id.toString());
  if (params.district_id) q.append('district_id', params.district_id.toString());
  if (params.project_id) q.append('project_id', params.project_id);
  if (params.category) q.append('category', params.category);
  if (params.status) q.append('status', params.status);
  if (params.current_stage) q.append('current_stage', params.current_stage);
  if (params.date_from) q.append('date_from', params.date_from);
  if (params.date_to) q.append('date_to', params.date_to);
  const str = q.toString();
  return str ? `?${str}` : '';
};

export const analyticsApi = {
  getSummary: async (params?: AnalyticsFilterParams): Promise<AnalyticsSummaryData> => {
    return apiClient<AnalyticsSummaryData>(`/analytics/summary${buildQueryString(params)}`);
  },

  getStateAnalytics: async (params?: AnalyticsFilterParams): Promise<{ items: StateAnalyticsItemData[]; total: number }> => {
    return apiClient<{ items: StateAnalyticsItemData[]; total: number }>(`/analytics/states${buildQueryString(params)}`);
  },

  getProjectAnalytics: async (params?: AnalyticsFilterParams): Promise<{ items: ProjectAnalyticsItemData[]; total: number }> => {
    return apiClient<{ items: ProjectAnalyticsItemData[]; total: number }>(`/analytics/projects${buildQueryString(params)}`);
  },

  getLandAnalytics: async (params?: AnalyticsFilterParams): Promise<LandAnalyticsResponseData> => {
    return apiClient<LandAnalyticsResponseData>(`/analytics/land${buildQueryString(params)}`);
  },

  getCompensationAnalytics: async (params?: AnalyticsFilterParams): Promise<CompensationAnalyticsResponseData> => {
    return apiClient<CompensationAnalyticsResponseData>(`/analytics/compensation${buildQueryString(params)}`);
  },

  getWorkflowAnalytics: async (): Promise<WorkflowAnalyticsResponseData> => {
    return apiClient<WorkflowAnalyticsResponseData>('/analytics/workflow');
  },

  getDelayAnalytics: async (): Promise<DelayAnalyticsResponseData> => {
    return apiClient<DelayAnalyticsResponseData>('/analytics/delays');
  },
};

