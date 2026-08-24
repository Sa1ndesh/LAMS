import { apiClient } from './api';
import { NotificationItem } from '../types';

export interface NotificationListResponseData {
  items: NotificationItem[];
  unread_count: number;
}

export const notificationsApi = {
  getNotifications: async (): Promise<NotificationListResponseData> => {
    return apiClient<NotificationListResponseData>('/notifications');
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    return apiClient<{ unread_count: number }>('/notifications/unread-count');
  },

  markRead: async (id: string): Promise<NotificationItem> => {
    return apiClient<NotificationItem>(`/notifications/${id}/read`, {
      method: 'PUT',
    });
  },

  markAllRead: async (): Promise<{ message: string }> => {
    return apiClient<{ message: string }>('/notifications/read-all', {
      method: 'PUT',
    });
  },
};

