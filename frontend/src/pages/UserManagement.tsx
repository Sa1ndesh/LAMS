import React, { useState } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { SearchBar } from '../components/ui/SearchBar';
import { FilterBar } from '../components/ui/FilterBar';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { mockUsers } from '../data/mockData';
import { User, UserRole } from '../types';
import { UserPlus, Shield, Edit, Key } from 'lucide-react';

export const UserManagement: React.FC = () => {
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);

  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('LAND_ACQUISITION_OFFICER');
  const [newDept, setNewDept] = useState('');

  const filteredUsers = mockUsers.filter((u) => {
    const matchesSearch =
      u.fullName.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase());
    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const handleUserSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`Authorized user account for ${newName} created!`);
    setIsAddUserOpen(false);
  };

  const columns: Column<User>[] = [
    {
      header: 'Officer Name & Email',
      cell: (row) => (
        <div>
          <div className="font-bold text-xs text-lams-primary">{row.fullName}</div>
          <div className="text-xs text-lams-muted">{row.email}</div>
        </div>
      ),
    },
    {
      header: 'Assigned Role',
      cell: (row) => (
        <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-50 text-lams-primary border border-blue-200 flex items-center gap-1.5 w-fit">
          <Shield className="h-3 w-3 text-lams-secondary" /> {row.role}
        </span>
      ),
    },
    {
      header: 'Jurisdiction / Department',
      cell: (row) => (
        <div className="text-xs font-medium text-slate-800">
          {row.department || `${row.district}, ${row.state}`}
        </div>
      ),
    },
    {
      header: 'Account Status',
      cell: () => <StatusBadge status="ON_TRACK" size="sm" />,
    },
    {
      header: 'Actions',
      cell: (row) => (
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" icon={<Edit className="h-3.5 w-3.5" />} onClick={() => alert(`Edit ${row.fullName}`)}>
            Edit Role
          </Button>
          <Button variant="ghost" size="sm" icon={<Key className="h-3.5 w-3.5" />} onClick={() => alert(`Reset password for ${row.email}`)}>
            Reset Password
          </Button>
        </div>
      ),
    },
  ];

  return (
    <PageContainer
      title="Role-Based User Access Control (RBAC)"
      description="Manage Government Officers, Administrative Roles & District Nodal Permissions"
      actions={
        <Button variant="primary" icon={<UserPlus className="h-4 w-4" />} onClick={() => setIsAddUserOpen(true)}>
          Add Authorized Officer
        </Button>
      }
    >
      <Card className="mb-6">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search officer name or email..."
            className="w-full md:w-80"
          />

          <FilterBar
            filters={[
              {
                key: 'role',
                label: 'Role',
                value: roleFilter,
                onChange: setRoleFilter,
                options: [
                  { label: 'SUPER_ADMIN', value: 'SUPER_ADMIN' },
                  { label: 'CENTRAL_MINISTRY', value: 'CENTRAL_MINISTRY' },
                  { label: 'STATE_AUTHORITY', value: 'STATE_AUTHORITY' },
                  { label: 'DISTRICT_ADMIN', value: 'DISTRICT_ADMIN' },
                  { label: 'LAND_ACQUISITION_OFFICER', value: 'LAND_ACQUISITION_OFFICER' },
                  { label: 'FIELD_OFFICER', value: 'FIELD_OFFICER' },
                  { label: 'PROJECT_IMPLEMENTING_AGENCY', value: 'PROJECT_IMPLEMENTING_AGENCY' },
                  { label: 'VIEWER', value: 'VIEWER' },
                ],
              },
            ]}
            onReset={() => {
              setSearch('');
              setRoleFilter('ALL');
            }}
          />
        </div>
      </Card>

      <Card title="System User Accounts Directory">
        <Table data={filteredUsers} columns={columns} keyExtractor={(row) => row.id} />
      </Card>

      {/* Modal: Add User */}
      <Modal
        isOpen={isAddUserOpen}
        onClose={() => setIsAddUserOpen(false)}
        title="Add Authorized System User"
        subtitle="Create credentials and assign security role"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsAddUserOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleUserSubmit}>
              Create User Account
            </Button>
          </>
        }
      >
        <form onSubmit={handleUserSubmit} className="space-y-4 text-xs">
          <Input
            label="Full Name *"
            placeholder="e.g. Suresh Varma"
            required
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <Input
            label="Official Email *"
            type="email"
            placeholder="e.g. officer@lams.gov.in"
            required
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
          />
          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Assigned Role *</label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as UserRole)}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="SUPER_ADMIN">SUPER_ADMIN (National Administrator)</option>
              <option value="CENTRAL_MINISTRY">CENTRAL_MINISTRY (Ministry Officer)</option>
              <option value="STATE_AUTHORITY">STATE_AUTHORITY (State Nodal Officer)</option>
              <option value="DISTRICT_ADMIN">DISTRICT_ADMIN (District Magistrate)</option>
              <option value="LAND_ACQUISITION_OFFICER">LAND_ACQUISITION_OFFICER (Special LAO)</option>
              <option value="FIELD_OFFICER">FIELD_OFFICER (Survey Inspector)</option>
              <option value="PROJECT_IMPLEMENTING_AGENCY">PROJECT_IMPLEMENTING_AGENCY (NHAI/Railways)</option>
              <option value="VIEWER">VIEWER (Read Only)</option>
            </select>
          </div>
          <Input
            label="Department / Ministry"
            placeholder="e.g. Ministry of Road Transport and Highways"
            value={newDept}
            onChange={(e) => setNewDept(e.target.value)}
          />
        </form>
      </Modal>
    </PageContainer>
  );
};
