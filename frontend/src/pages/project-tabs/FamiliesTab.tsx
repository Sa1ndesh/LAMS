import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { StatCard } from '../../components/ui/StatCard';
import { Table, Column } from '../../components/ui/Table';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { SearchBar } from '../../components/ui/SearchBar';
import { FilterBar } from '../../components/ui/FilterBar';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../hooks/useAuth';
import { AffectedFamily, Project } from '../../types';
import { Users, Home, CheckCircle2, Clock, Plus, Edit, Trash2 } from 'lucide-react';

export const FamiliesTab: React.FC = () => {
  const { project } = useOutletContext<{ project: Project }>();
  const { affectedFamilies, addAffectedFamily, updateAffectedFamily, deleteAffectedFamily } = useApp();
  const { canManageFamilies } = useAuth();

  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [rrFilter, setRrFilter] = useState('ALL');

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedFam, setSelectedFam] = useState<AffectedFamily | null>(null);

  // Form Fields
  const [headName, setHeadName] = useState('');
  const [villageName, setVillageName] = useState(project?.village || '');
  const [membersCount, setMembersCount] = useState('4');
  const [category, setCategory] = useState<AffectedFamily['category']>('OBC');
  const [isDisplaced, setIsDisplaced] = useState(true);
  const [rrStatus, setRrStatus] = useState<AffectedFamily['rrStatus']>('Eligible');
  const [famError, setFamError] = useState('');

  const families = affectedFamilies.filter((f) => f.projectId === project.id);

  const filteredFamilies = families.filter((f) => {
    const q = search.toLowerCase();
    const matchesSearch =
      f.headOfFamily.toLowerCase().includes(q) ||
      f.familyRefId.toLowerCase().includes(q) ||
      f.village.toLowerCase().includes(q);

    const matchesCategory = categoryFilter === 'ALL' || f.category === categoryFilter;
    const matchesRr = rrFilter === 'ALL' || f.rrStatus === rrFilter;

    return matchesSearch && matchesCategory && matchesRr;
  });

  const totalAffected = families.length;
  const totalDisplaced = families.filter((f) => f.isDisplaced).length;
  const totalCompleted = families.filter((f) => f.rrStatus === 'Resettled' || f.rrStatus === 'Completed').length;
  const totalPending = totalAffected - totalCompleted;

  const openCreateModal = () => {
    setHeadName('');
    setVillageName(project?.village || '');
    setMembersCount('4');
    setCategory('OBC');
    setIsDisplaced(true);
    setRrStatus('Eligible');
    setFamError('');
    setIsCreateOpen(true);
  };

  const openEditModal = (f: AffectedFamily) => {
    setSelectedFam(f);
    setHeadName(f.headOfFamily);
    setVillageName(f.village);
    setMembersCount(f.familyMembersCount.toString());
    setCategory(f.category);
    setIsDisplaced(f.isDisplaced);
    setRrStatus(f.rrStatus);
    setFamError('');
    setIsEditOpen(true);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFamError('');

    if (!headName.trim()) return setFamError('Head of Family name is required.');
    const count = parseInt(membersCount, 10);
    if (isNaN(count) || count <= 0) return setFamError('Family members count must be at least 1.');

    addAffectedFamily({
      projectId: project.id,
      village: villageName.trim() || project.village,
      headOfFamily: headName.trim(),
      familyMembersCount: count,
      category,
      isDisplaced,
      rrStatus,
    });

    setIsCreateOpen(false);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFam) return;
    setFamError('');

    const count = parseInt(membersCount, 10);
    if (isNaN(count) || count <= 0) return setFamError('Family members count must be at least 1.');

    updateAffectedFamily(selectedFam.id, {
      headOfFamily: headName.trim(),
      village: villageName.trim(),
      familyMembersCount: count,
      category,
      isDisplaced,
      rrStatus,
    });

    setIsEditOpen(false);
    setSelectedFam(null);
  };

  const handleConfirmDelete = () => {
    if (selectedFam) {
      deleteAffectedFamily(selectedFam.id);
      setIsDeleteOpen(false);
      setSelectedFam(null);
    }
  };

  const columns: Column<AffectedFamily>[] = [
    {
      header: 'Family Reference ID',
      cell: (row) => <span className="font-mono text-xs font-bold text-lams-primary">{row.familyRefId}</span>,
    },
    {
      header: 'Head of Family',
      cell: (row) => (
        <div>
          <div className="font-semibold text-xs text-lams-dark">{row.headOfFamily}</div>
          <div className="text-[11px] text-lams-muted">{row.familyMembersCount} Members • Category: {row.category}</div>
        </div>
      ),
    },
    {
      header: 'Village',
      cell: (row) => <span className="text-xs text-slate-800 font-medium">{row.village}</span>,
    },
    {
      header: 'Displacement Status',
      cell: (row) => (
        <span
          className={`px-2 py-0.5 text-xs font-semibold rounded ${
            row.isDisplaced ? 'bg-amber-50 text-amber-800 border border-amber-200' : 'bg-slate-100 text-slate-700'
          }`}
        >
          {row.isDisplaced ? 'Displaced' : 'Non-Displaced'}
        </span>
      ),
    },
    {
      header: 'R&R Package Status',
      cell: (row) => <StatusBadge status={row.rrStatus} />,
    },
    {
      header: 'Actions',
      cell: (row) => (
        canManageFamilies && (
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              icon={<Edit className="h-3.5 w-3.5" />}
              onClick={() => openEditModal(row)}
            >
              Edit
            </Button>
            <Button
              variant="ghost"
              size="sm"
              icon={<Trash2 className="h-3.5 w-3.5 text-red-600" />}
              onClick={() => {
                setSelectedFam(row);
                setIsDeleteOpen(true);
              }}
            />
          </div>
        )
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Affected Families"
          value={totalAffected}
          subtitle="Identified in Census"
          icon={Users}
          colorScheme="blue"
        />
        <StatCard
          title="Displaced Families"
          value={totalDisplaced}
          subtitle="Requiring Housing Site"
          icon={Home}
          colorScheme="amber"
        />
        <StatCard
          title="R&R Completed"
          value={totalCompleted}
          subtitle="Resettled / Paid"
          icon={CheckCircle2}
          colorScheme="emerald"
        />
        <StatCard
          title="R&R Pending"
          value={totalPending}
          subtitle="Assistance in Process"
          icon={Clock}
          colorScheme="purple"
        />
      </div>

      <Card>
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search family ref, head name, village..."
            className="w-full md:w-80"
          />

          <div className="flex items-center gap-3">
            <FilterBar
              filters={[
                {
                  key: 'category',
                  label: 'Category',
                  value: categoryFilter,
                  onChange: setCategoryFilter,
                  options: [
                    { label: 'SC', value: 'SC' },
                    { label: 'ST', value: 'ST' },
                    { label: 'OBC', value: 'OBC' },
                    { label: 'General', value: 'General' },
                  ],
                },
              ]}
              onReset={() => {
                setSearch('');
                setCategoryFilter('ALL');
                setRrFilter('ALL');
              }}
            />

            {canManageFamilies && (
              <Button variant="primary" size="sm" icon={<Plus className="h-4 w-4" />} onClick={openCreateModal}>
                Add Affected Family
              </Button>
            )}
          </div>
        </div>
      </Card>

      <Card title="Affected Families & R&R Census Register">
        <Table data={filteredFamilies} columns={columns} keyExtractor={(row) => row.id} emptyMessage="No affected family records." />
      </Card>

      {/* Modal: Add Affected Family */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register Affected Family"
        subtitle="Add family baseline census details"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateSubmit}>
              Save Family Record
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit} className="space-y-3.5 text-xs">
          {famError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg font-medium">
              {famError}
            </div>
          )}

          <Input
            label="Head of Family Name *"
            placeholder="e.g. Rameshwar Rao"
            required
            value={headName}
            onChange={(e) => setHeadName(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Village Name *"
              required
              value={villageName}
              onChange={(e) => setVillageName(e.target.value)}
            />
            <Input
              label="Family Members Count *"
              type="number"
              required
              value={membersCount}
              onChange={(e) => setMembersCount(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-lams-dark mb-1">Social Category *</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as AffectedFamily['category'])}
                className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
              >
                <option value="General">General</option>
                <option value="OBC">OBC</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-lams-dark mb-1">Displacement Status *</label>
              <select
                value={isDisplaced ? 'YES' : 'NO'}
                onChange={(e) => setIsDisplaced(e.target.value === 'YES')}
                className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
              >
                <option value="YES">Displaced</option>
                <option value="NO">Non-Displaced</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">R&R Assistance Status *</label>
            <select
              value={rrStatus}
              onChange={(e) => setRrStatus(e.target.value as AffectedFamily['rrStatus'])}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="Identified">Identified</option>
              <option value="Eligible">Eligible</option>
              <option value="Assistance Disbursed">Assistance Disbursed</option>
              <option value="Resettled">Resettled</option>
              <option value="Completed">Completed</option>
            </select>
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Family */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Update Family R&R Record"
        subtitle={`Family Ref #${selectedFam?.familyRefId}`}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleEditSubmit}>
              Save Updates
            </Button>
          </>
        }
      >
        <form onSubmit={handleEditSubmit} className="space-y-3.5 text-xs">
          <Input
            label="Head of Family Name *"
            required
            value={headName}
            onChange={(e) => setHeadName(e.target.value)}
          />

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">R&R Assistance Status *</label>
            <select
              value={rrStatus}
              onChange={(e) => setRrStatus(e.target.value as AffectedFamily['rrStatus'])}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="Identified">Identified</option>
              <option value="Eligible">Eligible</option>
              <option value="Assistance Disbursed">Assistance Disbursed</option>
              <option value="Resettled">Resettled</option>
              <option value="Completed">Completed</option>
            </select>
          </div>
        </form>
      </Modal>

      {/* Modal: Delete Family */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Confirm Deletion"
        subtitle={`Family Ref #${selectedFam?.familyRefId}`}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" onClick={handleConfirmDelete}>
              Delete Record
            </Button>
          </>
        }
      >
        <p className="text-xs text-slate-600">Are you sure you want to remove this family census entry?</p>
      </Modal>
    </div>
  );
};
