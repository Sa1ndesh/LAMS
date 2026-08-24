import { apiClient } from './api';
import { ProjectGISSummary, GeoJSONFeatureCollection, MapBounds } from '../types/gis';

export const gisApi = {
  getProjectGISSummary: async (projectId: string): Promise<ProjectGISSummary> => {
    return apiClient<ProjectGISSummary>(`/gis/projects/${projectId}`);
  },

  getProjectParcelsGeoJSON: async (projectId: string, bounds?: MapBounds): Promise<GeoJSONFeatureCollection> => {
    let query = '';
    if (bounds) {
      query = `?min_lon=${bounds.min_lon}&min_lat=${bounds.min_lat}&max_lon=${bounds.max_lon}&max_lat=${bounds.max_lat}`;
    }
    return apiClient<GeoJSONFeatureCollection>(`/gis/projects/${projectId}/parcels${query}`);
  },

  updateParcelGeometry: async (
    projectId: string,
    surveyNumber: string,
    coordinates: number[][],
    areaHectares?: number
  ): Promise<{ message: string }> => {
    return apiClient<{ message: string }>(`/gis/projects/${projectId}/parcels/geometry`, {
      method: 'POST',
      body: JSON.stringify({
        survey_number: surveyNumber,
        coordinates,
        area_hectares: areaHectares,
      }),
    });
  },
};

