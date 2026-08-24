import { apiClient, getToken, BASE_URL } from './api';

export interface DocumentResponseData {
  id: string;
  project_id: string;
  document_name: string;
  category: string;
  file_reference: string;
  stored_file_name?: string;
  file_path?: string;
  mime_type?: string;
  file_size?: number;
  description?: string;
  version: string;
  uploaded_by: string;
  upload_date: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponseData {
  items: DocumentResponseData[];
  total: number;
}

export const documentsApi = {
  getDocumentsByProject: async (
    projectId: string,
    search?: string,
    category?: string
  ): Promise<DocumentListResponseData> => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (category && category !== 'ALL') params.append('category', category);

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    return apiClient<DocumentListResponseData>(`/projects/${projectId}/documents${queryStr}`);
  },

  getDocument: async (documentId: string): Promise<DocumentResponseData> => {
    return apiClient<DocumentResponseData>(`/documents/${documentId}`);
  },

  uploadDocument: async (projectId: string, formData: FormData): Promise<DocumentResponseData> => {
    return apiClient<DocumentResponseData>(`/projects/${projectId}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
  },

  downloadDocument: async (documentId: string, filename: string): Promise<void> => {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}/documents/${documentId}/download`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to download document file.');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'document.pdf';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  previewDocumentUrl: (documentId: string): string => {
    const token = getToken();
    return `${BASE_URL}/documents/${documentId}/preview?token=${token || ''}`;
  },

  deleteDocument: async (id: string): Promise<void> => {
    return apiClient<void>(`/documents/${id}`, {
      method: 'DELETE',
    });
  },
};
