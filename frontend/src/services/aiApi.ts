import { apiClient } from './api';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type RecommendationPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface RiskFactorData {
  factor: string;
  impact: string;
  severity: string;
  description: string;
  metric: string;
  current_value: any;
  threshold: any;
}

export interface RecommendationData {
  priority: RecommendationPriority;
  title: string;
  description: string;
  related_factor: string;
}

export interface ProjectRiskData {
  project_id: string;
  project_code: string;
  project_name: string;
  risk_score: number;
  risk_level: RiskLevel;
  confidence: number;
  factors: RiskFactorData[];
  recommendations: RecommendationData[];
  generated_at: string;
}

export interface BottleneckDetailData {
  category: string;
  title: string;
  severity: string;
  description: string;
  impact_points: number;
}

export interface ProjectInsightData {
  project_id: string;
  project_name: string;
  risk_score: number;
  risk_level: RiskLevel;
  bottlenecks: BottleneckDetailData[];
  recommendations: RecommendationData[];
  summary: string;
}

export interface HighRiskProjectData {
  project_id: string;
  project_code: string;
  project_name: string;
  state: string;
  category: string;
  current_stage: string;
  risk_score: number;
  risk_level: RiskLevel;
  top_risk_factor: string;
  recommended_action: string;
}

export interface AIOverviewData {
  total_projects: number;
  low_risk_projects: number;
  medium_risk_projects: number;
  high_risk_projects: number;
  critical_projects: number;
  average_risk_score: number;
  highest_risk_projects: HighRiskProjectData[];
  national_insights: string[];
}

export const aiApi = {
  getProjectRisk: async (projectId: string): Promise<ProjectRiskData> => {
    return apiClient<ProjectRiskData>(`/ai/projects/${projectId}/risk`);
  },

  getProjectInsights: async (projectId: string): Promise<ProjectInsightData> => {
    return apiClient<ProjectInsightData>(`/ai/projects/${projectId}/insights`);
  },

  getAIOverview: async (): Promise<AIOverviewData> => {
    return apiClient<AIOverviewData>('/ai/overview');
  },

  getHighRiskProjects: async (): Promise<HighRiskProjectData[]> => {
    return apiClient<HighRiskProjectData[]>('/ai/projects/high-risk');
  },
};

