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

export const mapBackendProjectToFrontend = (raw: any): Project => {
  if (!raw) return raw;
  return {
    id: raw.id || '',
    projectCode: raw.project_code || raw.projectCode || '',
    name: raw.name || '',
    projectType: raw.category || raw.projectType || 'Infrastructure',
    ministry: raw.ministry || '',
    implementingAgency: raw.implementing_agency || raw.implementingAgency || '',
    state: raw.state_name || raw.state || 'Karnataka',
    district: raw.district_name || raw.district || 'Bengaluru',
    village: raw.village || '',
    landProposedHectares: typeof raw.land_proposed_hectares === 'number' ? raw.land_proposed_hectares : (raw.landProposedHectares || 0),
    landAcquiredHectares: typeof raw.land_acquired_hectares === 'number' ? raw.land_acquired_hectares : (raw.landAcquiredHectares || 0),
    budgetInr: typeof raw.budget_inr === 'number' ? raw.budget_inr : (raw.budgetInr || 0),
    currentStage: raw.current_stage || raw.currentStage || 'Proposal',
    startDate: raw.start_date || raw.startDate || '',
    targetCompletionDate: raw.target_completion_date || raw.targetCompletionDate || '',
    status: raw.status || 'ON_TRACK',
    description: raw.description || '',
  };
};

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
    const res = await apiClient<any>(`/projects${queryString}`);
    if (res && Array.isArray(res.items)) {
      return {
        ...res,
        items: res.items.map(mapBackendProjectToFrontend),
      };
    }
    return res;
  },

  getProjectById: async (id: string): Promise<Project> => {
    const res = await apiClient<any>(`/projects/${id}`);
    return mapBackendProjectToFrontend(res);
  },

  createProject: async (projectData: Partial<Project>): Promise<Project> => {
    const res = await apiClient<any>('/projects', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
    return mapBackendProjectToFrontend(res);
  },

  updateProject: async (id: string, projectData: Partial<Project>): Promise<Project> => {
    const res = await apiClient<any>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(projectData),
    });
    return mapBackendProjectToFrontend(res);
  },

  deleteProject: async (id: string): Promise<void> => {
    return apiClient<void>(`/projects/${id}`, {
      method: 'DELETE',
    });
  },
};

