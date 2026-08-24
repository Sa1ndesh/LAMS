import { apiClient } from './api';
import { AffectedFamily } from '../types';

export interface FamilyListResponseData {
  items: AffectedFamily[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const familiesApi = {
  getFamiliesByProject: async (projectId: string, search?: string): Promise<FamilyListResponseData> => {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return apiClient<FamilyListResponseData>(`/projects/${projectId}/families${query}`);
  },

  createFamily: async (projectId: string, data: Partial<AffectedFamily>): Promise<AffectedFamily> => {
    return apiClient<AffectedFamily>(`/projects/${projectId}/families`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateFamily: async (id: string, data: Partial<AffectedFamily>): Promise<AffectedFamily> => {
    return apiClient<AffectedFamily>(`/families/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  deleteFamily: async (id: string): Promise<void> => {
    return apiClient<void>(`/families/${id}`, {
      method: 'DELETE',
    });
  },
};

