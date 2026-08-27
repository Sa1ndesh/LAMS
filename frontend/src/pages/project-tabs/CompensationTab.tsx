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
import { CompensationRecord, Project } from '../../types';
import { IndianRupee, CheckCircle2, Clock, Plus, Edit } from 'lucide-react';

import { mockCompensationRecords } from '../../data/mockData';

export const CompensationTab: React.FC = () => {
  const { project } = useOutletContext<{ project: Project }>();
  const { compensationRecords, parcels, addCompensationRecord, updateCompensationRecord } = useApp();
  const { canManageCompensation } = useAuth();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedComp, setSelectedComp] = useState<CompensationRecord | null>(null);

  // Form Fields
  const [formParcelId, setFormParcelId] = useState('');
  const [formAssessed, setFormAssessed] = useState('');
  const [formApproved, setFormApproved] = useState('');
  const [formDisbursed, setFormDisbursed] = useState('');
  const [formStatus, setFormStatus] = useState<CompensationRecord['paymentStatus']>('Assessed');
  const [formDate, setFormDate] = useState('');
  const [compError, setCompError] = useState('');

  const projectParcels = parcels.filter((p) => p.projectId === project?.id || String(p.projectId) === String(project?.id));
  const directRecords = compensationRecords.filter((r) => r.projectId === project?.id || String(r.projectId) === String(project?.id));
  const records = directRecords.length > 0 ? directRecords : mockCompensationRecords;

  const filteredRecords = records.filter((r) => {
    const parcel = parcels.find((p) => p.id === r.parcelId);
    const q = search.toLowerCase();
    const matchesSearch =
      parcel?.surveyNumber.toLowerCase().includes(q) ||
      parcel?.ownerName.toLowerCase().includes(q) ||
      parcel?.parcelCode.toLowerCase().includes(q);

    const matchesStatus = statusFilter === 'ALL' || r.paymentStatus === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const totalAssessed = records.reduce((acc, r) => acc + r.assessedAmountInr, 0);
  const totalApproved = records.reduce((acc, r) => acc + r.approvedAmountInr, 0);
  const totalDisbursed = records.reduce((acc, r) => acc + r.disbursedAmountInr, 0);
  const totalPending = records.reduce((acc, r) => acc + r.pendingAmountInr, 0);

  const formatInr = (val: number) => `₹ ${(val / 100000).toLocaleString('en-IN')} Lakhs`;

  const openCreateModal = () => {
    setFormParcelId(projectParcels[0]?.id || '');
    setFormAssessed('');
    setFormApproved('');
    setFormDisbursed('0');
    setFormStatus('Assessed');
    setFormDate('');
    setCompError('');
    setIsModalOpen(true);
  };

  const openEditModal = (r: CompensationRecord) => {
    setSelectedComp(r);
    setFormAssessed((r.assessedAmountInr / 100000).toString());
    setFormApproved((r.approvedAmountInr / 100000).toString());
    setFormDisbursed((r.disbursedAmountInr / 100000).toString());
    setFormStatus(r.paymentStatus);
    setFormDate(r.paymentDate || '');
    setCompError('');
    setIsEditModalOpen(true);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCompError('');

    const assessedLakhs = parseFloat(formAssessed);
    const approvedLakhs = parseFloat(formApproved);
    const disbursedLakhs = parseFloat(formDisbursed) || 0;

    if (isNaN(assessedLakhs) || assessedLakhs <= 0) return setCompError('Valid Assessed Amount is required.');
    if (isNaN(approvedLakhs) || approvedLakhs < 0) return setCompError('Valid Approved Amount is required.');

    addCompensationRecord({
      projectId: project.id,
      parcelId: formParcelId || projectParcels[0]?.id || 'pcl-101',
      assessedAmountInr: assessedLakhs * 100000,
      approvedAmountInr: approvedLakhs * 100000,
      disbursedAmountInr: disbursedLakhs * 100000,
      paymentStatus: formStatus,
      paymentDate: formDate || undefined,
    });

    setIsModalOpen(false);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedComp) return;
    setCompError('');

    const assessedLakhs = parseFloat(formAssessed);
    const approvedLakhs = parseFloat(formApproved);
    const disbursedLakhs = parseFloat(formDisbursed) || 0;

    updateCompensationRecord(selectedComp.id, {
      assessedAmountInr: assessedLakhs * 100000,
      approvedAmountInr: approvedLakhs * 100000,
      disbursedAmountInr: disbursedLakhs * 100000,
      paymentStatus: formStatus,
      paymentDate: formDate || undefined,
    });

    setIsEditModalOpen(false);
    setSelectedComp(null);
  };

  const columns: Column<CompensationRecord>[] = [
    {
      header: 'Parcel & Survey Reference',
      cell: (row) => {
        const parcel = parcels.find((p) => p.id === row.parcelId);
        return (
          <div>
            <div className="font-bold text-xs text-lams-primary">Survey No. {parcel?.surveyNumber || '104/A'}</div>
            <div className="text-xs text-lams-muted">{parcel?.ownerName || 'Landowner'}</div>
          </div>
        );
      },
    },
    {
      header: 'Assessed Amount',
      cell: (row) => <span className="font-medium text-xs text-slate-800">{formatInr(row.assessedAmountInr)}</span>,
    },
    {
      header: 'Approved Amount',
      cell: (row) => <span className="font-semibold text-xs text-lams-primary">{formatInr(row.approvedAmountInr)}</span>,
    },
    {
      header: 'Disbursed Amount',
      cell: (row) => <span className="font-bold text-xs text-emerald-700">{formatInr(row.disbursedAmountInr)}</span>,
    },
    {
      header: 'Pending Balance',
      cell: (row) => <span className="font-semibold text-xs text-amber-700">{formatInr(row.pendingAmountInr)}</span>,
    },
    {
      header: 'Payment Status',
      cell: (row) => <StatusBadge status={row.paymentStatus} />,
    },
    {
      header: 'Disbursement Date',
      cell: (row) => <span className="text-xs text-lams-muted font-medium">{row.paymentDate || 'Pending'}</span>,
    },
    {
      header: 'Actions',
      cell: (row) => (
        canManageCompensation && (
          <Button
            variant="outline"
            size="sm"
            icon={<Edit className="h-3.5 w-3.5" />}
            onClick={() => openEditModal(row)}
          >
            Update
          </Button>
        )
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Dynamic Stat Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Assessed Amount"
          value={`₹ ${(totalAssessed / 10000000).toFixed(2)} Cr`}
          subtitle="Collector Evaluated Amount"
          icon={IndianRupee}
          colorScheme="blue"
        />
        <StatCard
          title="Approved Amount"
          value={`₹ ${(totalApproved / 10000000).toFixed(2)} Cr`}
          subtitle="Sanctioned Treasury Allocation"
          icon={CheckCircle2}
          colorScheme="indigo"
        />
        <StatCard
          title="Disbursed Amount"
          value={`₹ ${(totalDisbursed / 10000000).toFixed(2)} Cr`}
          subtitle="Direct Bank Transfer"
          icon={CheckCircle2}
          colorScheme="emerald"
        />
        <StatCard
          title="Pending Balance"
          value={`₹ ${(totalPending / 10000000).toFixed(2)} Cr`}
          subtitle="Approved Minus Disbursed"
          icon={Clock}
          colorScheme="amber"
        />
      </div>

      <Card>
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search survey #, owner name..."
            className="w-full md:w-80"
          />

          <div className="flex items-center gap-3">
            <FilterBar
              filters={[
                {
                  key: 'status',
                  label: 'Payment Status',
                  value: statusFilter,
                  onChange: setStatusFilter,
                  options: [
                    { label: 'Assessed', value: 'Assessed' },
                    { label: 'Approved', value: 'Approved' },
                    { label: 'Partially Disbursed', value: 'Partially Disbursed' },
                    { label: 'Disbursed', value: 'Disbursed' },
                    { label: 'Pending', value: 'Pending' },
                  ],
                },
              ]}
              onReset={() => {
                setSearch('');
                setStatusFilter('ALL');
              }}
            />

            {canManageCompensation && (
              <Button variant="primary" size="sm" icon={<Plus className="h-4 w-4" />} onClick={openCreateModal}>
                Add Ledger Record
              </Button>
            )}
          </div>
        </div>
      </Card>

      <Card title="Parcel Compensation Disbursement Ledger">
        <Table data={filteredRecords} columns={columns} keyExtractor={(row) => row.id} emptyMessage="No compensation records." />
      </Card>

      {/* Modal: Add Compensation Record */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Compensation Assessment"
        subtitle="Register collector land valuation and treasury sanction"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateSubmit}>
              Save Ledger Record
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit} className="space-y-3.5 text-xs">
          {compError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg font-medium">
              {compError}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Target Land Parcel *</label>
            <select
              value={formParcelId}
              onChange={(e) => setFormParcelId(e.target.value)}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              {projectParcels.map((p) => (
                <option key={p.id} value={p.id}>
                  Survey #{p.surveyNumber} ({p.ownerName} - {p.areaHectares} Ha)
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Assessed Amount (₹ Lakhs) *"
              type="number"
              step="0.1"
              placeholder="e.g. 45"
              required
              value={formAssessed}
              onChange={(e) => setFormAssessed(e.target.value)}
            />
            <Input
              label="Approved Amount (₹ Lakhs) *"
              type="number"
              step="0.1"
              placeholder="e.g. 45"
              required
              value={formApproved}
              onChange={(e) => setFormApproved(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Disbursed Amount (₹ Lakhs)"
              type="number"
              step="0.1"
              placeholder="e.g. 20"
              value={formDisbursed}
              onChange={(e) => setFormDisbursed(e.target.value)}
            />
            <div>
              <label className="block text-xs font-semibold text-lams-dark mb-1">Payment Status *</label>
              <select
                value={formStatus}
                onChange={(e) => setFormStatus(e.target.value as CompensationRecord['paymentStatus'])}
                className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
              >
                <option value="Assessed">Assessed</option>
                <option value="Approved">Approved</option>
                <option value="Partially Disbursed">Partially Disbursed</option>
                <option value="Disbursed">Disbursed</option>
                <option value="Pending">Pending</option>
              </select>
            </div>
          </div>

          <Input
            label="Disbursement Date"
            type="date"
            value={formDate}
            onChange={(e) => setFormDate(e.target.value)}
          />
        </form>
      </Modal>

      {/* Modal: Edit/Update Compensation */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Update Compensation Disbursement"
        subtitle="Record direct bank payment and update status"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleEditSubmit}>
              Update Record
            </Button>
          </>
        }
      >
        <form onSubmit={handleEditSubmit} className="space-y-3.5 text-xs">
          <Input
            label="Disbursed Amount (₹ Lakhs) *"
            type="number"
            step="0.1"
            required
            value={formDisbursed}
            onChange={(e) => setFormDisbursed(e.target.value)}
          />

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Payment Status *</label>
            <select
              value={formStatus}
              onChange={(e) => setFormStatus(e.target.value as CompensationRecord['paymentStatus'])}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="Assessed">Assessed</option>
              <option value="Approved">Approved</option>
              <option value="Partially Disbursed">Partially Disbursed</option>
              <option value="Disbursed">Disbursed</option>
              <option value="Pending">Pending</option>
            </select>
          </div>

          <Input
            label="Disbursement Payment Date *"
            type="date"
            required
            value={formDate}
            onChange={(e) => setFormDate(e.target.value)}
          />
        </form>
      </Modal>
    </div>
  );
};
