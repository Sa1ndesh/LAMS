import { apiClient } from './api';
import { LandParcel } from '../types';

export interface ParcelListResponseData {
  items: LandParcel[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const parcelsApi = {
  getParcelsByProject: async (projectId: string, search?: string): Promise<ParcelListResponseData> => {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return apiClient<ParcelListResponseData>(`/projects/${projectId}/parcels${query}`);
  },

  createParcel: async (projectId: string, parcelData: Partial<LandParcel>): Promise<LandParcel> => {
    return apiClient<LandParcel>(`/projects/${projectId}/parcels`, {
      method: 'POST',
      body: JSON.stringify(parcelData),
    });
  },

  updateParcel: async (id: string, parcelData: Partial<LandParcel>): Promise<LandParcel> => {
    return apiClient<LandParcel>(`/parcels/${id}`, {
      method: 'PUT',
      body: JSON.stringify(parcelData),
    });
  },

  deleteParcel: async (id: string): Promise<void> => {
    return apiClient<void>(`/parcels/${id}`, {
      method: 'DELETE',
    });
  },
};

