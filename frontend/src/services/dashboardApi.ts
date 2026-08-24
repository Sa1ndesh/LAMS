import { apiClient } from './api';

export interface StateProgressData {
  state: string;
  target: number;
  acquired: number;
  percentage: number;
}

export interface StageDistributionData {
  stage: string;
  count: number;
}

export interface DashboardSummaryData {
  total_projects: number;
  land_proposed_hectares: number;
  land_acquired_hectares: number;
  acquisition_percentage: number;
  compensation_assessed_inr: number;
  compensation_disbursed_inr: number;
  compensation_pending_inr: number;
  affected_families_count: number;
  displaced_families_count: number;
  delayed_projects_count: number;
  state_progress: StateProgressData[];
  stage_distribution: StageDistributionData[];
}

export const dashboardApi = {
  getSummary: async (): Promise<DashboardSummaryData> => {
    return apiClient<DashboardSummaryData>('/dashboard/summary');
  },
};

