import { apiClient } from './api';
import { Project } from '../types';

export interface ProjectListParams {
  search?: string;
  state_id?: number;
  district_id?: number;
  category?: string;
  status?: string;
  current_stage?: string;
  page?: number;
  page_size?: number;
}

export interface ProjectListResponseData {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const projectsApi = {
  getProjects: async (params: ProjectListParams = {}): Promise<ProjectListResponseData> => {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.state_id) query.append('state_id', params.state_id.toString());
    if (params.district_id) query.append('district_id', params.district_id.toString());
    if (params.category) query.append('category', params.category);
    if (params.status) query.append('status', params.status);
    if (params.current_stage) query.append('current_stage', params.current_stage);
    if (params.page) query.append('page', params.page.toString());
    if (params.page_size) query.append('page_size', params.page_size.toString());

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return apiClient<ProjectListResponseData>(`/projects${queryString}`);
  },

  getProjectById: async (id: string): Promise<Project> => {
    return apiClient<Project>(`/projects/${id}`);
  },

  createProject: async (projectData: Partial<Project>): Promise<Project> => {
    return apiClient<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  },

  updateProject: async (id: string, projectData: Partial<Project>): Promise<Project> => {
    return apiClient<Project>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(projectData),
    });
  },

  deleteProject: async (id: string): Promise<void> => {
    return apiClient<void>(`/projects/${id}`, {
      method: 'DELETE',
    });
  },
};

