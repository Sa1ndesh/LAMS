import { apiClient } from './api';

export interface UserResponseData {
  id: string;
  name: string;
  email: string;
  role: string;
  state_id?: number;
  district_id?: number;
  is_active: boolean;
}

export const usersApi = {
  getUsers: async (): Promise<UserResponseData[]> => {
    return apiClient<UserResponseData[]>('/users');
  },

  getUserById: async (id: string): Promise<UserResponseData> => {
    return apiClient<UserResponseData>(`/users/${id}`);
  },

  toggleUserStatus: async (id: string, isActive: boolean): Promise<UserResponseData> => {
    return apiClient<UserResponseData>(`/users/${id}/status?is_active=${isActive}`, {
      method: 'PUT',
    });
  },
};

