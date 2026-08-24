export interface GeoJSONPolygonGeometry {
  type: 'Polygon';
  coordinates: number[][][];
}

export interface GISParcelProperties {
  parcel_id: string;
  parcel_code: string;
  survey_number: string;
  area_hectares: number;
  land_type: string;
  acquisition_status: string;
  compensation_status: string;
  possession_status: string;
  village: string;
  taluk: string;
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: GeoJSONPolygonGeometry;
  properties: GISParcelProperties;
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

export interface ProjectGISSummary {
  project_id: string;
  project_name: string;
  project_code: string;
  parcel_count: number;
  acquired_area_hectares: number;
  bounding_box: [number, number, number, number]; // [min_lon, min_lat, max_lon, max_lat]
  geojson: GeoJSONFeatureCollection;
}

export interface MapBounds {
  min_lon: number;
  min_lat: number;
  max_lon: number;
  max_lat: number;
}

