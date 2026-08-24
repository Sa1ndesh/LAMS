import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { SearchBar } from '../components/ui/SearchBar';
import { FilterBar } from '../components/ui/FilterBar';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Table, Column } from '../components/ui/Table';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { EmptyState } from '../components/ui/EmptyState';
import { useApp } from '../context/AppContext';
import { useAuth } from '../hooks/useAuth';
import { Project } from '../types';
import { Plus, Eye, Edit, Trash2, AlertTriangle } from 'lucide-react';

export const ProjectsDirectory: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { projects, addProject, updateProject, deleteProject } = useApp();
  const { canCreateProject, canEditProject, canDeleteProject } = useAuth();

  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');

  // Handle URL query string search (e.g. /projects?search=metro)
  useEffect(() => {
    const querySearch = searchParams.get('search');
    if (querySearch) {
      setSearch(querySearch);
    }
  }, [searchParams]);

  // Modal States
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  // Form Fields
  const [formName, setFormName] = useState('');
  const [formCode, setFormCode] = useState('');
  const [formType, setFormType] = useState('Highways & Expressways');
  const [formMinistry, setFormMinistry] = useState('');
  const [formAgency, setFormAgency] = useState('');
  const [formState, setFormState] = useState('Karnataka');
  const [formDistrict, setFormDistrict] = useState('');
  const [formVillage, setFormVillage] = useState('');
  const [formProposedArea, setFormProposedArea] = useState('');
  const [formBudget, setFormBudget] = useState('');
  const [formStartDate, setFormStartDate] = useState('');
  const [formTargetDate, setFormTargetDate] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formError, setFormError] = useState('');

  // Reset Form
  const resetForm = () => {
    setFormName('');
    setFormCode('');
    setFormType('Highways & Expressways');
    setFormMinistry('');
    setFormAgency('');
    setFormState('Karnataka');
    setFormDistrict('');
    setFormVillage('');
    setFormProposedArea('');
    setFormBudget('');
    setFormStartDate('');
    setFormTargetDate('');
    setFormDescription('');
    setFormError('');
  };

  // Open Edit Modal
  const openEditModal = (p: Project) => {
    setSelectedProjectId(p.id);
    setFormName(p.name);
    setFormCode(p.projectCode);
    setFormType(p.projectType);
    setFormMinistry(p.ministry);
    setFormAgency(p.implementingAgency);
    setFormState(p.state);
    setFormDistrict(p.district);
    setFormVillage(p.village);
    setFormProposedArea(p.landProposedHectares.toString());
    setFormBudget((p.budgetInr / 10000000).toString());
    setFormStartDate(p.startDate);
    setFormTargetDate(p.targetCompletionDate);
    setFormDescription(p.description || '');
    setFormError('');
    setIsEditOpen(true);
  };

  // Open Delete Modal
  const openDeleteModal = (id: string) => {
    setSelectedProjectId(id);
    setIsDeleteOpen(true);
  };

  // Form Validation & Submit (Create)
  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!formName.trim()) return setFormError('Project Name is required.');
    if (!formCode.trim()) return setFormError('Project Code is required.');
    if (!formMinistry.trim()) return setFormError('Ministry is required.');
    if (!formAgency.trim()) return setFormError('Implementing Agency is required.');
    if (!formDistrict.trim()) return setFormError('District is required.');
    if (!formVillage.trim()) return setFormError('Village is required.');

    const proposedAreaNum = parseFloat(formProposedArea);
    if (isNaN(proposedAreaNum) || proposedAreaNum <= 0) {
      return setFormError('Proposed Land Footprint must be a positive number.');
    }

    const budgetNum = parseFloat(formBudget);
    if (isNaN(budgetNum) || budgetNum <= 0) {
      return setFormError('Budget must be a positive number in ₹ Crores.');
    }

    if (!formStartDate || !formTargetDate) {
      return setFormError('Start Date and Target Completion Date are required.');
    }

    addProject({
      name: formName.trim(),
      projectCode: formCode.trim(),
      projectType: formType,
      ministry: formMinistry.trim(),
      implementingAgency: formAgency.trim(),
      state: formState,
      district: formDistrict.trim(),
      village: formVillage.trim(),
      landProposedHectares: proposedAreaNum,
      budgetInr: budgetNum * 10000000,
      currentStage: 'Proposal',
      startDate: formStartDate,
      targetCompletionDate: formTargetDate,
      description: formDescription.trim(),
    });

    setIsCreateOpen(false);
    resetForm();
  };

  // Form Submit (Edit)
  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId) return;
    setFormError('');

    const proposedAreaNum = parseFloat(formProposedArea);
    if (isNaN(proposedAreaNum) || proposedAreaNum <= 0) {
      return setFormError('Proposed Land Footprint must be a positive number.');
    }

    updateProject(selectedProjectId, {
      name: formName.trim(),
      projectType: formType,
      ministry: formMinistry.trim(),
      implementingAgency: formAgency.trim(),
      state: formState,
      district: formDistrict.trim(),
      village: formVillage.trim(),
      landProposedHectares: proposedAreaNum,
      startDate: formStartDate,
      targetCompletionDate: formTargetDate,
      description: formDescription.trim(),
    });

    setIsEditOpen(false);
    resetForm();
  };

  // Confirm Delete
  const handleConfirmDelete = () => {
    if (selectedProjectId) {
      deleteProject(selectedProjectId);
      setIsDeleteOpen(false);
      setSelectedProjectId(null);
    }
  };

  // Filtering Logic
  const filteredProjects = projects.filter((p) => {
    const q = search.toLowerCase();
    const matchesSearch =
      p.name.toLowerCase().includes(q) ||
      p.projectCode.toLowerCase().includes(q) ||
      p.district.toLowerCase().includes(q) ||
      p.state.toLowerCase().includes(q);

    const matchesState = stateFilter === 'ALL' || p.state === stateFilter;
    const matchesStatus = statusFilter === 'ALL' || p.status === statusFilter;
    const matchesType = typeFilter === 'ALL' || p.projectType === typeFilter;

    return matchesSearch && matchesState && matchesStatus && matchesType;
  });

  const columns: Column<Project>[] = [
    {
      header: 'Project Code & Name',
      cell: (row) => (
        <div>
          <button
            onClick={() => navigate(`/projects/${row.id}`)}
            className="font-bold text-xs text-lams-secondary hover:underline text-left block"
          >
            {row.name}
          </button>
          <span className="text-[11px] font-mono text-slate-500">{row.projectCode}</span>
        </div>
      ),
    },
    {
      header: 'Category',
      cell: (row) => <span className="text-xs font-medium text-slate-800">{row.projectType}</span>,
    },
    {
      header: 'Jurisdiction',
      cell: (row) => (
        <div className="text-xs">
          <div className="font-semibold text-lams-dark">{row.district}, {row.state}</div>
          <div className="text-lams-muted text-[11px]">Village: {row.village}</div>
        </div>
      ),
    },
    {
      header: 'Land Progress',
      cell: (row) => {
        const pct = row.landProposedHectares > 0 ? Math.round((row.landAcquiredHectares / row.landProposedHectares) * 100) : 0;
        return (
          <div className="w-36 text-xs">
            <ProgressBar value={pct} label={`${row.landAcquiredHectares} / ${row.landProposedHectares} Ha`} color="blue" size="sm" />
          </div>
        );
      },
    },
    {
      header: 'Stage',
      cell: (row) => <StatusBadge status={row.currentStage} />,
    },
    {
      header: 'Health Status',
      cell: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Actions',
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="sm"
            icon={<Eye className="h-3.5 w-3.5" />}
            onClick={() => navigate(`/projects/${row.id}`)}
          >
            View
          </Button>

          {canEditProject && (
            <Button
              variant="ghost"
              size="sm"
              icon={<Edit className="h-3.5 w-3.5 text-lams-secondary" />}
              onClick={() => openEditModal(row)}
            />
          )}

          {canDeleteProject && (
            <Button
              variant="ghost"
              size="sm"
              icon={<Trash2 className="h-3.5 w-3.5 text-red-600" />}
              onClick={() => openDeleteModal(row.id)}
            />
          )}
        </div>
      ),
    },
  ];

  return (
    <PageContainer
      title="National Projects Directory"
      description="Central Registry & Portfolio Management of Land Acquisition Projects Across India"
      actions={
        canCreateProject ? (
          <Button variant="primary" icon={<Plus className="h-4 w-4" />} onClick={() => { resetForm(); setIsCreateOpen(true); }}>
            Propose Project
          </Button>
        ) : undefined
      }
    >
      {/* Search & Filter Bar Card */}
      <Card className="mb-6">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search by project name, code, district..."
            className="w-full md:w-80"
          />

          <FilterBar
            filters={[
              {
                key: 'state',
                label: 'State',
                value: stateFilter,
                onChange: setStateFilter,
                options: [
                  { label: 'Karnataka', value: 'Karnataka' },
                  { label: 'Maharashtra', value: 'Maharashtra' },
                  { label: 'Gujarat', value: 'Gujarat' },
                  { label: 'Tamil Nadu', value: 'Tamil Nadu' },
                  { label: 'Rajasthan', value: 'Rajasthan' },
                ],
              },
              {
                key: 'status',
                label: 'Status',
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: 'On Track', value: 'ON_TRACK' },
                  { label: 'Delayed', value: 'DELAYED' },
                  { label: 'Critical', value: 'CRITICAL' },
                  { label: 'Completed', value: 'COMPLETED' },
                ],
              },
            ]}
            onReset={() => {
              setSearch('');
              setStateFilter('ALL');
              setStatusFilter('ALL');
              setTypeFilter('ALL');
            }}
          />
        </div>
      </Card>

      {/* Projects Table or Empty State */}
      {filteredProjects.length === 0 ? (
        <EmptyState
          title="No Matching Projects Found"
          description="No projects match your search query or filter selection."
          actionLabel="Clear Filters"
          onAction={() => {
            setSearch('');
            setStateFilter('ALL');
            setStatusFilter('ALL');
            setTypeFilter('ALL');
          }}
        />
      ) : (
        <Table data={filteredProjects} columns={columns} keyExtractor={(row) => row.id} />
      )}

      {/* Modal: Propose New Project */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Propose New Land Acquisition Project"
        subtitle="Submit a new infrastructure project for central verification"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateSubmit}>
              Submit Proposal
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit} className="space-y-3.5 text-xs">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg font-medium">
              {formError}
            </div>
          )}

          <Input
            label="Project Name *"
            placeholder="e.g. NH-48 Expressway Expansion"
            required
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Project Code *"
              placeholder="e.g. LAMS-KA-2026-099"
              required
              value={formCode}
              onChange={(e) => setFormCode(e.target.value)}
            />

            <div>
              <label className="block text-xs font-semibold text-lams-dark mb-1">Project Category *</label>
              <select
                value={formType}
                onChange={(e) => setFormType(e.target.value)}
                className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
              >
                <option value="Highways & Expressways">Highways & Expressways</option>
                <option value="Railways & Metro">Railways & Metro</option>
                <option value="Freight Rail Corridor">Freight Rail Corridor</option>
                <option value="Power & Energy">Power & Energy</option>
                <option value="Irrigation & Water Resources">Irrigation & Water Resources</option>
                <option value="Airport Infrastructure">Airport Infrastructure</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Nodal Ministry *"
              placeholder="e.g. Ministry of Road Transport"
              required
              value={formMinistry}
              onChange={(e) => setFormMinistry(e.target.value)}
            />
            <Input
              label="Implementing Agency *"
              placeholder="e.g. NHAI"
              required
              value={formAgency}
              onChange={(e) => setFormAgency(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-lams-dark mb-1">State *</label>
              <select
                value={formState}
                onChange={(e) => setFormState(e.target.value)}
                className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
              >
                <option value="Karnataka">Karnataka</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Gujarat">Gujarat</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
                <option value="Rajasthan">Rajasthan</option>
                <option value="Telangana">Telangana</option>
              </select>
            </div>
            <Input
              label="District *"
              placeholder="e.g. Bengaluru Urban"
              required
              value={formDistrict}
              onChange={(e) => setFormDistrict(e.target.value)}
            />
            <Input
              label="Village *"
              placeholder="e.g. Hoskote"
              required
              value={formVillage}
              onChange={(e) => setFormVillage(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Proposed Land (Hectares) *"
              type="number"
              step="0.01"
              placeholder="e.g. 450.50"
              required
              value={formProposedArea}
              onChange={(e) => setFormProposedArea(e.target.value)}
            />
            <Input
              label="Allocated Budget (₹ Crores) *"
              type="number"
              step="0.1"
              placeholder="e.g. 1250"
              required
              value={formBudget}
              onChange={(e) => setFormBudget(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Start Date *"
              type="date"
              required
              value={formStartDate}
              onChange={(e) => setFormStartDate(e.target.value)}
            />
            <Input
              label="Target Completion Date *"
              type="date"
              required
              value={formTargetDate}
              onChange={(e) => setFormTargetDate(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Project Description</label>
            <textarea
              rows={3}
              value={formDescription}
              onChange={(e) => setFormDescription(e.target.value)}
              placeholder="Overview of project alignment, scope, and right-of-way details..."
              className="w-full bg-white border border-lams-border rounded-lg p-2.5 text-xs text-lams-dark focus:outline-none focus:ring-1 focus:ring-lams-secondary"
            />
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Project */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Edit Project Details"
        subtitle={`Updating project record #${formCode}`}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleEditSubmit}>
              Save Changes
            </Button>
          </>
        }
      >
        <form onSubmit={handleEditSubmit} className="space-y-3.5 text-xs">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg font-medium">
              {formError}
            </div>
          )}

          <Input
            label="Project Name *"
            required
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Proposed Land (Hectares) *"
              type="number"
              step="0.01"
              required
              value={formProposedArea}
              onChange={(e) => setFormProposedArea(e.target.value)}
            />
            <div>
              <label className="block text-xs font-semibold text-lams-dark mb-1">State *</label>
              <select
                value={formState}
                onChange={(e) => setFormState(e.target.value)}
                className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
              >
                <option value="Karnataka">Karnataka</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Gujarat">Gujarat</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Start Date *"
              type="date"
              required
              value={formStartDate}
              onChange={(e) => setFormStartDate(e.target.value)}
            />
            <Input
              label="Target Completion Date *"
              type="date"
              required
              value={formTargetDate}
              onChange={(e) => setFormTargetDate(e.target.value)}
            />
          </div>
        </form>
      </Modal>

      {/* Modal: Delete Confirmation */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Confirm Project Deletion"
        subtitle="This action will remove the project and linked records from mock storage."
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" onClick={handleConfirmDelete}>
              Delete Project
            </Button>
          </>
        }
      >
        <div className="flex items-center gap-3 p-4 bg-red-50 text-red-800 rounded-xl border border-red-200 text-xs">
          <AlertTriangle className="h-6 w-6 text-red-600 shrink-0" />
          <p>Are you sure you want to permanently archive this project? Linked parcels and compensation ledgers will also be updated.</p>
        </div>
      </Modal>
    </PageContainer>
  );
};
