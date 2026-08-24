import { useAuthContext } from '../context/AuthContext';
import { UserRole } from '../types';

export const useAuth = () => {
  const { user, role, setUserRole, isAuthenticated, logout } = useAuthContext();

  const isSuperAdmin = role === 'SUPER_ADMIN';
  const isLao = role === 'LAND_ACQUISITION_OFFICER';
  const isDistrictAdmin = role === 'DISTRICT_ADMIN';
  const isViewer = role === 'VIEWER';

  // Permission Checks (Frontend Authorization Helpers)
  const canCreateProject = isSuperAdmin || role === 'CENTRAL_MINISTRY' || role === 'STATE_AUTHORITY';
  const canEditProject = isSuperAdmin || isLao || isDistrictAdmin;
  const canDeleteProject = isSuperAdmin;
  const canManageParcels = isSuperAdmin || isLao || role === 'FIELD_OFFICER';
  const canManageCompensation = isSuperAdmin || isLao || isDistrictAdmin;
  const canManageFamilies = isSuperAdmin || isLao || isDistrictAdmin;

  return {
    user,
    role,
    setRole: (r: UserRole) => setUserRole(r),
    isAuthenticated,
    logout,
    isSuperAdmin,
    isLao,
    isDistrictAdmin,
    isViewer,
    canCreateProject,
    canEditProject,
    canDeleteProject,
    canManageParcels,
    canManageCompensation,
    canManageFamilies,
  };
};
