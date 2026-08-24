import { apiClient } from './api';
import { TimelineMilestone } from '../types';

export interface MilestoneListResponseData {
  items: TimelineMilestone[];
  total: number;
}

export const milestonesApi = {
  getMilestonesByProject: async (projectId: string): Promise<MilestoneListResponseData> => {
    return apiClient<MilestoneListResponseData>(`/projects/${projectId}/milestones`);
  },

  createMilestone: async (projectId: string, data: Partial<TimelineMilestone>): Promise<TimelineMilestone> => {
    return apiClient<TimelineMilestone>(`/projects/${projectId}/milestones`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateMilestone: async (id: string, data: Partial<TimelineMilestone>): Promise<TimelineMilestone> => {
    return apiClient<TimelineMilestone>(`/milestones/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

