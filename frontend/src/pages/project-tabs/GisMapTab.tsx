import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { MapContainer, TileLayer, Polygon, Popup, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { useApp } from '../../context/AppContext';
import { Project, LandParcel } from '../../types';
import { gisApi } from '../../services/gisApi';
import { MapPin, Compass, Crosshair, X } from 'lucide-react';

// Fix Leaflet Default Icon Path
delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Map Events Component for Coordinate Capture
const MapEventsHandler: React.FC<{
  onMapClick: (lat: number, lng: number) => void;
  isCaptureMode: boolean;
}> = ({ onMapClick, isCaptureMode }) => {
  useMapEvents({
    click(e: L.LeafletMouseEvent) {
      if (isCaptureMode) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
};

// Fit Bounds Helper Component
const FitBoundsHelper: React.FC<{ bounds: [number, number, number, number] }> = ({ bounds }) => {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length === 4) {
      const [minLon, minLat, maxLon, maxLat] = bounds;
      if (minLon !== maxLon && minLat !== maxLat) {
        map.fitBounds([
          [minLat, minLon],
          [maxLat, maxLon],
        ]);
      }
    }
  }, [bounds, map]);
  return null;
};

export const GisMapTab: React.FC = () => {
  const { project } = useOutletContext<{ project: Project }>();
  const { parcels } = useApp();

  const projectParcels = parcels.filter((p) => p.projectId === project.id);
  const [selectedParcelId, setSelectedParcelId] = useState<string | null>(projectParcels[0]?.id || null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [isCaptureMode, setIsCaptureMode] = useState<boolean>(false);
  const [capturedCoord, setCapturedCoord] = useState<{ lat: number; lng: number } | null>(null);
  const [mapSummary, setMapSummary] = useState<{
    boundingBox: [number, number, number, number];
  } | null>(null);

  // Load project GIS summary from API
  useEffect(() => {
    const fetchGis = async () => {
      try {
        const summary = await gisApi.getProjectGISSummary(project.id);
        if (summary && summary.bounding_box) {
          setMapSummary({ boundingBox: summary.bounding_box });
        }
      } catch (err) {
        console.warn('GIS Summary API fallback:', err);
      }
    };
    fetchGis();
  }, [project.id]);

  const selectedParcel = projectParcels.find((p) => p.id === selectedParcelId) || projectParcels[0];

  // Map Filter application
  const filteredParcels = projectParcels.filter((p) => {
    if (statusFilter === 'ALL') return true;
    return p.acquisitionStatus.toUpperCase() === statusFilter.toUpperCase();
  });

  // Calculate default center lat/lng
  const centerLat = selectedParcel?.latitude || 12.9716;
  const centerLng = selectedParcel?.longitude || 77.5946;

  // Polygon styling generator
  const getParcelStyle = (statusStr: string, isSelected: boolean) => {
    let fillColor = '#1261A3';
    let color = '#002046';

    const s = statusStr.toUpperCase();
    if (s.includes('ACQUIRED')) {
      fillColor = '#059669';
      color = '#047857';
    } else if (s.includes('NOTIFIED')) {
      fillColor = '#1261A3';
      color = '#0B4A7B';
    } else if (s.includes('PROPOSED') || s.includes('PENDING')) {
      fillColor = '#D97706';
      color = '#B45309';
    } else if (s.includes('DISPUTED')) {
      fillColor = '#DC2626';
      color = '#991B1B';
    }

    return {
      fillColor,
      fillOpacity: isSelected ? 0.6 : 0.35,
      color: isSelected ? '#38BDF8' : color,
      weight: isSelected ? 3 : 2,
    };
  };

  // Build polygon coordinates array around parcel lat/lng
  const getParcelPolygonCoords = (p: LandParcel): [number, number][] => {
    const lat = p.latitude || 12.9716;
    const lng = p.longitude || 77.5946;
    const delta = 0.003;
    return [
      [lat - delta, lng - delta],
      [lat - delta, lng + delta],
      [lat + delta, lng + delta],
      [lat + delta, lng - delta],
    ];
  };

  const handleMapClick = (lat: number, lng: number) => {
    setCapturedCoord({ lat: Number(lat.toFixed(6)), lng: Number(lng.toFixed(6)) });
  };

  return (
    <div className="space-y-6">
      {/* Control Header Bar */}
      <Card className="py-3 px-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-lams-primary">
            <Compass className="h-4 w-4 text-lams-secondary" />
            <span>Interactive Leaflet Map • PostGIS Cadastral Layer (EPSG:4326)</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-lams-border rounded-lg px-2.5 py-1 text-xs font-medium text-lams-dark focus:outline-none"
            >
              <option value="ALL">Filter: All Statuses</option>
              <option value="PROPOSED">Filter: Proposed</option>
              <option value="NOTIFIED">Filter: Notified</option>
              <option value="ACQUIRED">Filter: Acquired</option>
              <option value="DISPUTED">Filter: Disputed</option>
            </select>

            <Button
              variant={isCaptureMode ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setIsCaptureMode(!isCaptureMode)}
              icon={<Crosshair className="h-3.5 w-3.5" />}
            >
              {isCaptureMode ? 'Capturing Coords' : 'Capture Mode'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Main Map Split Shell */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Side: Interactive Map Container */}
        <div className="lg:col-span-3 bg-slate-900 rounded-2xl border border-slate-800 relative overflow-hidden min-h-[500px] flex flex-col justify-between shadow-2xl">
          {/* Real Leaflet Map */}
          <div className="h-[520px] w-full relative z-0">
            <MapContainer
              center={[centerLat, centerLng]}
              zoom={13}
              scrollWheelZoom={true}
              className="h-full w-full rounded-2xl"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              <MapEventsHandler onMapClick={handleMapClick} isCaptureMode={isCaptureMode} />

              {mapSummary && <FitBoundsHelper bounds={mapSummary.boundingBox} />}

              {/* Render Parcel Polygons */}
              {filteredParcels.map((pcl) => {
                const polyCoords = getParcelPolygonCoords(pcl);
                const isSelected = pcl.id === selectedParcelId;
                const style = getParcelStyle(pcl.acquisitionStatus, isSelected);

                return (
                  <Polygon
                    key={pcl.id}
                    positions={polyCoords}
                    pathOptions={style}
                    eventHandlers={{
                      click: () => setSelectedParcelId(pcl.id),
                    }}
                  >
                    <Popup>
                      <div className="p-3 space-y-1.5 text-xs max-w-xs">
                        <div className="font-bold text-lams-primary border-b pb-1 flex justify-between items-center">
                          <span>Survey #{pcl.surveyNumber}</span>
                          <span className="text-[10px] text-lams-secondary font-mono">{pcl.parcelCode}</span>
                        </div>
                        <div><span className="text-slate-500">Village:</span> {pcl.village}, {pcl.taluk}</div>
                        <div><span className="text-slate-500">Area:</span> <strong className="text-emerald-700">{pcl.areaHectares} Ha</strong></div>
                        <div><span className="text-slate-500">Land Type:</span> {pcl.landType}</div>
                        <div><span className="text-slate-500">Owner:</span> {pcl.ownerName || 'State Record'}</div>
                        <div className="pt-1"><StatusBadge status={pcl.acquisitionStatus} size="sm" /></div>
                      </div>
                    </Popup>
                  </Polygon>
                );
              })}

              {/* Marker for Coordinate Capture */}
              {capturedCoord && (
                <Marker position={[capturedCoord.lat, capturedCoord.lng]}>
                  <Popup>
                    <div className="p-2 text-xs font-semibold">
                      <div>Captured Coordinate:</div>
                      <div className="font-mono text-sky-600">{capturedCoord.lat}° N, {capturedCoord.lng}° E</div>
                    </div>
                  </Popup>
                </Marker>
              )}
            </MapContainer>
          </div>

          {/* Coordinate Capture Banner */}
          {capturedCoord && (
            <div className="absolute top-4 left-4 z-[400] bg-slate-900/90 text-white p-3 rounded-xl border border-sky-400/40 shadow-xl flex items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-2">
                <Crosshair className="h-4 w-4 text-sky-400 animate-spin" />
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-bold">Captured Map Point</div>
                  <div className="font-mono font-bold text-sky-300">{capturedCoord.lat}° N, {capturedCoord.lng}° E</div>
                </div>
              </div>
              <button
                onClick={() => setCapturedCoord(null)}
                className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Map Legend Overlay */}
          <div className="absolute bottom-4 left-4 right-4 z-[400] flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 backdrop-blur-md p-3 rounded-xl border border-slate-700/60 text-xs text-white">
            <div className="flex items-center gap-4">
              <span className="font-semibold text-slate-300">Status Legend:</span>
              <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-emerald-500"></span> Acquired</span>
              <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-sky-500"></span> Notified</span>
              <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-amber-500"></span> Proposed</span>
              <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-red-500"></span> Disputed</span>
            </div>
            <span className="text-[11px] text-slate-400">PostGIS Engine • EPSG:4326</span>
          </div>
        </div>

        {/* Right Side: Selected Parcel Info Inspector */}
        <Card title="Parcel GIS Inspector" className="lg:col-span-1">
          {selectedParcel ? (
            <div className="space-y-4 text-xs">
              <div className="p-3 bg-blue-50/70 rounded-xl border border-blue-100">
                <span className="text-[10px] font-bold uppercase tracking-wider text-lams-muted">Selected Parcel Code</span>
                <h4 className="font-mono text-sm font-extrabold text-lams-primary mt-0.5">{selectedParcel.parcelCode}</h4>
                <span className="text-xs font-semibold text-slate-700 block mt-1">Survey No. {selectedParcel.surveyNumber}</span>
              </div>

              <div className="space-y-2 pt-2 border-t border-lams-border">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-lams-muted font-medium">Landowner Name</span>
                  <span className="font-semibold text-lams-dark">{selectedParcel.ownerName}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-lams-muted font-medium">Land Area</span>
                  <span className="font-bold text-lams-primary">{selectedParcel.areaHectares} Hectares</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-lams-muted font-medium">Classification</span>
                  <span className="font-semibold text-slate-700">{selectedParcel.landType}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-lams-muted font-medium">Village / Taluk</span>
                  <span className="font-medium text-slate-800">{selectedParcel.village}, {selectedParcel.taluk}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-lams-muted font-medium">Center Coordinates</span>
                  <span className="font-mono text-[11px] text-slate-700">{selectedParcel.latitude}° N, {selectedParcel.longitude}° E</span>
                </div>
              </div>

              <div className="pt-3 border-t border-lams-border space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-lams-muted">Acquisition Status</span>
                <StatusBadge status={selectedParcel.acquisitionStatus} size="md" />
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-lams-muted text-xs">
              No parcel selected. Click a parcel polygon on the map.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
