import React, { useState } from 'react';
import { useParams, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { LifecycleTracker } from '../components/ui/LifecycleTracker';
import { Tabs } from '../components/ui/Tabs';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { useApp } from '../context/AppContext';
import { useAuth } from '../hooks/useAuth';
import { ArrowLeft, Plus, Download, Bell, Layers, FileText, Users, DollarSign, Map, Clock, CheckCircle2 } from 'lucide-react';
import { LifecycleStage } from '../types';

export const ProjectLayout: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { projects, parcels, affectedFamilies, updateProjectStage, addParcel } = useApp();
  const { canManageParcels, canEditProject } = useAuth();

  const project = projects.find((p) => p.id === id) || projects[0];
  const projectParcels = parcels.filter((p) => p.projectId === project?.id || String(p.projectId) === String(project?.id));
  const projectFamilies = affectedFamilies.filter((f) => f.projectId === project?.id || String(f.projectId) === String(project?.id));

  const [isAddParcelOpen, setIsAddParcelOpen] = useState(false);
  const [newSurveyNumber, setNewSurveyNumber] = useState('');
  const [newArea, setNewArea] = useState('');
  const [newLandType, setNewLandType] = useState('Agricultural');
  const [newOwner, setNewOwner] = useState('');
  const [newTaluk, setNewTaluk] = useState('');
  const [newVillage, setNewVillage] = useState(project?.village || '');
  const [newLat, setNewLat] = useState('12.9698');
  const [newLng, setNewLng] = useState('77.7499');
  const [parcelError, setParcelError] = useState('');

  // Lifecycle stage confirmation modal
  const [isStageModalOpen, setIsStageModalOpen] = useState(false);
  const [pendingStage, setPendingStage] = useState<LifecycleStage | null>(null);
  const [stageSuccess, setStageSuccess] = useState(false);

  // Define Sub-tabs
  const tabs = [
    { id: 'overview', label: 'Overview', icon: <Layers className="h-4 w-4" /> },
    { id: 'parcels', label: 'Land Parcels', count: projectParcels.length || 3, icon: <Map className="h-4 w-4" /> },
    { id: 'notifications', label: 'Notifications', count: 2, icon: <Bell className="h-4 w-4" /> },
    { id: 'compensation', label: 'Compensation', icon: <DollarSign className="h-4 w-4" /> },
    { id: 'families', label: 'Affected Families', count: projectFamilies.length || 3, icon: <Users className="h-4 w-4" /> },
    { id: 'documents', label: 'Documents', count: 4, icon: <FileText className="h-4 w-4" /> },
    { id: 'timeline', label: 'Timeline', icon: <Clock className="h-4 w-4" /> },
    { id: 'map', label: 'GIS Map', icon: <Map className="h-4 w-4" /> },
  ];

  const pathParts = location.pathname.split('/');
  const currentTab = pathParts[3] || 'overview';

  const handleTabChange = (tabId: string) => {
    if (tabId === 'overview') {
      navigate(`/projects/${project.id}`);
    } else {
      navigate(`/projects/${project.id}/${tabId}`);
    }
  };

  const handleStageSelect = (selectedStage: LifecycleStage) => {
    if (!canEditProject) {
      // Show permission notice inline — no window.alert
      setPendingStage(null);
      setIsStageModalOpen(false);
      return;
    }
    setPendingStage(selectedStage);
    setIsStageModalOpen(true);
  };

  const handleStageConfirm = () => {
    if (pendingStage) {
      updateProjectStage(project.id, pendingStage);
      setStageSuccess(true);
      setTimeout(() => setStageSuccess(false), 3000);
    }
    setIsStageModalOpen(false);
    setPendingStage(null);
  };

  const handleAddParcelSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setParcelError('');

    if (!newSurveyNumber.trim()) return setParcelError('Survey Number is required.');
    const areaNum = parseFloat(newArea);
    if (isNaN(areaNum) || areaNum <= 0) return setParcelError('Area must be a positive number in Hectares.');

    const latNum = parseFloat(newLat);
    const lngNum = parseFloat(newLng);
    if (isNaN(latNum) || isNaN(lngNum)) return setParcelError('Valid latitude and longitude coordinates are required.');

    addParcel({
      projectId: project.id,
      surveyNumber: newSurveyNumber.trim(),
      state: project.state,
      district: project.district,
      taluk: newTaluk.trim() || 'Central Taluk',
      village: newVillage.trim() || project.village,
      areaHectares: areaNum,
      landType: newLandType,
      ownerName: newOwner.trim() || 'Public Landowner',
      acquisitionStatus: 'Proposed',
      compensationStatus: 'Pending',
      possessionStatus: 'Not Taken',
      latitude: latNum,
      longitude: lngNum,
    });

    setIsAddParcelOpen(false);
    setNewSurveyNumber('');
    setNewArea('');
    setNewOwner('');
    setParcelError('');
  };

  if (!project) {
    return (
      <PageContainer title="Project Not Found">
        <Card className="text-center py-12">
          <p className="text-sm text-lams-muted">The requested project ID does not exist in central state.</p>
          <Button variant="primary" size="sm" className="mt-4" onClick={() => navigate('/projects')}>
            Back to Directory
          </Button>
        </Card>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={project.name}
      description={`Project Code: ${project.projectCode} • ${project.district}, ${project.state} • Village: ${project.village}`}
      actions={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigate('/projects')}
          >
            Back
          </Button>
          <Button
            variant="outline"
            size="sm"
            icon={<Download className="h-4 w-4" />}
            onClick={() => alert(`Demo Download: Report exported for ${project.projectCode}`)}
          >
            Export
          </Button>
          {canManageParcels && (
            <Button
              variant="primary"
              size="sm"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setIsAddParcelOpen(true)}
            >
              Add Parcel
            </Button>
          )}
        </div>
      }
    >
      {/* 9-Stage Acquisition Lifecycle Tracker Bar */}
      <div className="mb-6 space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-lams-muted px-1">
          <span>Acquisition Lifecycle Progress (Click stage to advance)</span>
          <StatusBadge status={project.currentStage} size="md" />
        </div>
        <LifecycleTracker
          currentStage={project.currentStage}
          onStageSelect={handleStageSelect}
        />
        {stageSuccess && (
          <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold shadow-sm animate-pulse">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>Lifecycle stage updated successfully!</span>
          </div>
        )}
        {!canEditProject && (
          <p className="text-[11px] text-amber-600 font-medium px-1">
            ⚠️ Your current role does not have permission to change the lifecycle stage.
          </p>
        )}
      </div>

      {/* Sub-Tab Navigation Bar */}
      <Card className="mb-6 py-0 px-4">
        <Tabs tabs={tabs} activeTab={currentTab} onChange={handleTabChange} />
      </Card>

      {/* Sub-Route Content */}
      <Outlet context={{ project }} />

      {/* Modal: Confirm Stage Advance */}
      <Modal
        isOpen={isStageModalOpen}
        onClose={() => { setIsStageModalOpen(false); setPendingStage(null); }}
        title="Advance Acquisition Stage"
        subtitle={`Project: ${project.name} (${project.projectCode})`}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => { setIsStageModalOpen(false); setPendingStage(null); }}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" icon={<CheckCircle2 className="h-4 w-4" />} onClick={handleStageConfirm}>
              Confirm Stage Change
            </Button>
          </>
        }
      >
        <div className="space-y-3 text-sm text-slate-700">
          <p>You are about to advance the project lifecycle stage to:</p>
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <span className="font-bold text-lams-secondary text-base">{pendingStage}</span>
          </div>
          <p className="text-xs text-lams-muted">
            Current stage: <span className="font-semibold text-slate-800">{project.currentStage}</span>
            <br />
            This action will be recorded in the project audit log.
          </p>
        </div>
      </Modal>

      {/* Modal: Register New Land Parcel */}
      <Modal
        isOpen={isAddParcelOpen}
        onClose={() => setIsAddParcelOpen(false)}
        title="Register New Land Parcel"
        subtitle={`Adding parcel record under ${project.name} (${project.projectCode})`}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsAddParcelOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleAddParcelSubmit}>
              Submit Parcel Record
            </Button>
          </>
        }
      >
        <form onSubmit={handleAddParcelSubmit} className="space-y-3.5 text-xs">
          {parcelError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg font-medium">
              {parcelError}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Survey Number *"
              placeholder="e.g. 112/3-B"
              required
              value={newSurveyNumber}
              onChange={(e) => setNewSurveyNumber(e.target.value)}
            />
            <Input
              label="Area (Hectares) *"
              type="number"
              step="0.01"
              placeholder="e.g. 2.45"
              required
              value={newArea}
              onChange={(e) => setNewArea(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-lams-dark mb-1">Land Classification *</label>
              <select
                value={newLandType}
                onChange={(e) => setNewLandType(e.target.value)}
                className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
              >
                <option value="Agricultural">Agricultural</option>
                <option value="Commercial">Commercial</option>
                <option value="Residential">Residential</option>
                <option value="Forest">Forest Land</option>
                <option value="Government">Government Public Land</option>
              </select>
            </div>

            <Input
              label="Landowner Reference Name"
              placeholder="e.g. Venkatesh Gowda"
              value={newOwner}
              onChange={(e) => setNewOwner(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Taluk *"
              placeholder="e.g. Hoskote Taluk"
              value={newTaluk}
              onChange={(e) => setNewTaluk(e.target.value)}
            />
            <Input
              label="Village *"
              placeholder="e.g. Kannur"
              value={newVillage}
              onChange={(e) => setNewVillage(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Latitude *"
              type="number"
              step="0.0001"
              value={newLat}
              onChange={(e) => setNewLat(e.target.value)}
            />
            <Input
              label="Longitude *"
              type="number"
              step="0.0001"
              value={newLng}
              onChange={(e) => setNewLng(e.target.value)}
            />
          </div>
        </form>
      </Modal>
    </PageContainer>
  );
};
