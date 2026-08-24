import { apiClient } from './api';
import { CompensationRecord } from '../types';

export interface CompensationListResponseData {
  items: CompensationRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const compensationApi = {
  getCompensationByProject: async (projectId: string): Promise<CompensationListResponseData> => {
    return apiClient<CompensationListResponseData>(`/projects/${projectId}/compensation`);
  },

  createCompensation: async (projectId: string, data: Partial<CompensationRecord>): Promise<CompensationRecord> => {
    return apiClient<CompensationRecord>(`/projects/${projectId}/compensation`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateCompensation: async (id: string, data: Partial<CompensationRecord>): Promise<CompensationRecord> => {
    return apiClient<CompensationRecord>(`/compensation/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

