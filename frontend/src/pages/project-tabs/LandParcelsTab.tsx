import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { SearchBar } from '../../components/ui/SearchBar';
import { FilterBar } from '../../components/ui/FilterBar';
import { Table, Column } from '../../components/ui/Table';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { EmptyState } from '../../components/ui/EmptyState';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../hooks/useAuth';
import { LandParcel, Project } from '../../types';
import { Eye, Edit, Trash2, CheckCircle2 } from 'lucide-react';

export const LandParcelsTab: React.FC = () => {
  const { project } = useOutletContext<{ project: Project }>();
  const { parcels, updateParcel, deleteParcel } = useApp();
  const { canManageParcels } = useAuth();

  const [search, setSearch] = useState('');
  const [landTypeFilter, setLandTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Edit / Details Modal States
  const [selectedParcel, setSelectedParcel] = useState<LandParcel | null>(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  const [editAcqStatus, setEditAcqStatus] = useState<LandParcel['acquisitionStatus']>('Proposed');
  const [editCompStatus, setEditCompStatus] = useState<LandParcel['compensationStatus']>('Pending');
  const [editPossStatus, setEditPossStatus] = useState<LandParcel['possessionStatus']>('Not Taken');

  const projectParcels = parcels.filter((p) => p.projectId === project.id);

  const filteredParcels = projectParcels.filter((p) => {
    const q = search.toLowerCase();
    const matchesSearch =
      p.surveyNumber.toLowerCase().includes(q) ||
      p.ownerName.toLowerCase().includes(q) ||
      p.parcelCode.toLowerCase().includes(q) ||
      p.village.toLowerCase().includes(q);

    const matchesType = landTypeFilter === 'ALL' || p.landType === landTypeFilter;
    const matchesStatus = statusFilter === 'ALL' || p.acquisitionStatus === statusFilter;

    return matchesSearch && matchesType && matchesStatus;
  });

  const openEditModal = (p: LandParcel) => {
    setSelectedParcel(p);
    setEditAcqStatus(p.acquisitionStatus);
    setEditCompStatus(p.compensationStatus);
    setEditPossStatus(p.possessionStatus);
    setIsEditOpen(true);
  };

  const openDeleteModal = (p: LandParcel) => {
    setSelectedParcel(p);
    setIsDeleteOpen(true);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedParcel) return;

    updateParcel(selectedParcel.id, {
      acquisitionStatus: editAcqStatus,
      compensationStatus: editCompStatus,
      possessionStatus: editPossStatus,
    });

    setIsEditOpen(false);
    setSelectedParcel(null);
  };

  const handleConfirmDelete = () => {
    if (selectedParcel) {
      deleteParcel(selectedParcel.id);
      setIsDeleteOpen(false);
      setSelectedParcel(null);
    }
  };

  const columns: Column<LandParcel>[] = [
    {
      header: 'Parcel Code & Survey #',
      cell: (row) => (
        <div>
          <div className="font-mono text-xs font-bold text-lams-primary">{row.parcelCode}</div>
          <div className="text-xs font-semibold text-slate-700">Survey No. {row.surveyNumber}</div>
        </div>
      ),
    },
    {
      header: 'Location & Village',
      cell: (row) => (
        <div className="text-xs">
          <div className="font-medium text-lams-dark">{row.village}, {row.taluk}</div>
          <div className="text-lams-muted text-[11px]">{row.district}, {row.state}</div>
        </div>
      ),
    },
    {
      header: 'Area & Type',
      cell: (row) => (
        <div className="text-xs">
          <span className="font-bold text-lams-primary">{row.areaHectares} Ha</span>
          <div className="text-lams-muted text-[11px]">{row.landType}</div>
        </div>
      ),
    },
    {
      header: 'Landowner Reference',
      cell: (row) => <span className="text-xs font-medium text-slate-800">{row.ownerName}</span>,
    },
    {
      header: 'Acquisition Stage',
      cell: (row) => <StatusBadge status={row.acquisitionStatus} />,
    },
    {
      header: 'Compensation',
      cell: (row) => <StatusBadge status={row.compensationStatus} />,
    },
    {
      header: 'Possession',
      cell: (row) => <StatusBadge status={row.possessionStatus} />,
    },
    {
      header: 'Actions',
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="sm"
            icon={<Eye className="h-3.5 w-3.5" />}
            onClick={() => openEditModal(row)}
          >
            Inspect
          </Button>

          {canManageParcels && (
            <>
              <Button
                variant="ghost"
                size="sm"
                icon={<Edit className="h-3.5 w-3.5 text-lams-secondary" />}
                onClick={() => openEditModal(row)}
              />
              <Button
                variant="ghost"
                size="sm"
                icon={<Trash2 className="h-3.5 w-3.5 text-red-600" />}
                onClick={() => openDeleteModal(row)}
              />
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search survey number, owner name, parcel code..."
            className="w-full md:w-80"
          />

          <FilterBar
            filters={[
              {
                key: 'landType',
                label: 'Land Type',
                value: landTypeFilter,
                onChange: setLandTypeFilter,
                options: [
                  { label: 'Agricultural', value: 'Agricultural' },
                  { label: 'Commercial', value: 'Commercial' },
                  { label: 'Residential', value: 'Residential' },
                  { label: 'Forest', value: 'Forest' },
                  { label: 'Government', value: 'Government' },
                ],
              },
              {
                key: 'status',
                label: 'Status',
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: 'Proposed', value: 'Proposed' },
                  { label: 'Surveyed', value: 'Surveyed' },
                  { label: 'Notified', value: 'Notified' },
                  { label: 'Awarded', value: 'Awarded' },
                  { label: 'Acquired', value: 'Acquired' },
                ],
              },
            ]}
            onReset={() => {
              setSearch('');
              setLandTypeFilter('ALL');
              setStatusFilter('ALL');
            }}
          />
        </div>
      </Card>

      {filteredParcels.length === 0 ? (
        <EmptyState
          title="No Land Parcels Match Search"
          description="There are currently no land parcels matching your survey query or filter."
          actionLabel="Clear Filters"
          onAction={() => {
            setSearch('');
            setLandTypeFilter('ALL');
            setStatusFilter('ALL');
          }}
        />
      ) : (
        <Table data={filteredParcels} columns={columns} keyExtractor={(row) => row.id} />
      )}

      {/* Modal: Update Parcel Status */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Update Parcel Status"
        subtitle={`Survey No. ${selectedParcel?.surveyNumber} (${selectedParcel?.parcelCode})`}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleEditSubmit}>
              Save Status Updates
            </Button>
          </>
        }
      >
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Acquisition Stage *</label>
            <select
              value={editAcqStatus}
              onChange={(e) => setEditAcqStatus(e.target.value as LandParcel['acquisitionStatus'])}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="Proposed">Proposed</option>
              <option value="Verified">Verified</option>
              <option value="Surveyed">Surveyed</option>
              <option value="Notified">Notified</option>
              <option value="Awarded">Awarded</option>
              <option value="Acquired">Acquired</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Compensation Status *</label>
            <select
              value={editCompStatus}
              onChange={(e) => setEditCompStatus(e.target.value as LandParcel['compensationStatus'])}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="Pending">Pending</option>
              <option value="Assessed">Assessed</option>
              <option value="Approved">Approved</option>
              <option value="Disbursed">Disbursed</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Possession Status *</label>
            <select
              value={editPossStatus}
              onChange={(e) => setEditPossStatus(e.target.value as LandParcel['possessionStatus'])}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="Not Taken">Not Taken</option>
              <option value="Demarcated">Demarcated</option>
              <option value="Taken">Taken</option>
            </select>
          </div>
        </form>
      </Modal>

      {/* Modal: Delete Parcel */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Confirm Parcel Deletion"
        subtitle={`Survey No. ${selectedParcel?.surveyNumber}`}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" onClick={handleConfirmDelete}>
              Delete Parcel Record
            </Button>
          </>
        }
      >
        <p className="text-xs text-slate-600">
          Are you sure you want to remove Survey #{selectedParcel?.surveyNumber} from this project?
        </p>
      </Modal>
    </div>
  );
};
