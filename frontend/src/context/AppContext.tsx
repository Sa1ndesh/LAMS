import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  Project,
  LandParcel,
  CompensationRecord,
  AffectedFamily,
  DocumentItem,
  TimelineMilestone,
  NotificationItem,
  User,
  UserRole,
  LifecycleStage,
} from '../types';
import {
  mockProjects,
  mockParcels,
  mockCompensationRecords,
  mockAffectedFamilies,
  mockDocuments,
  mockTimeline,
  mockNotifications,
  mockUsers,
} from '../data/mockData';
import { projectsApi } from '../services/projectsApi';
import { parcelsApi } from '../services/parcelsApi';
import { compensationApi } from '../services/compensationApi';
import { familiesApi } from '../services/familiesApi';
import { documentsApi } from '../services/documentsApi';
import { milestonesApi } from '../services/milestonesApi';
import { notificationsApi } from '../services/notificationsApi';
import { getToken } from '../services/api';
import { useAuthContext } from './AuthContext';

interface AppContextType {
  currentUser: User;
  setCurrentUserRole: (role: UserRole) => void;
  projects: Project[];
  parcels: LandParcel[];
  compensationRecords: CompensationRecord[];
  affectedFamilies: AffectedFamily[];
  documents: DocumentItem[];
  milestones: TimelineMilestone[];
  notifications: NotificationItem[];
  isLoading: boolean;
  error: string | null;

  // Refetch utility
  refreshData: () => Promise<void>;

  // Actions
  addProject: (p: Omit<Project, 'id' | 'landAcquiredHectares' | 'status'>) => Promise<void>;
  updateProject: (id: string, updates: Partial<Project>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  updateProjectStage: (id: string, stage: LifecycleStage) => Promise<void>;

  addParcel: (p: Omit<LandParcel, 'id' | 'parcelCode'>) => Promise<void>;
  updateParcel: (id: string, updates: Partial<LandParcel>) => Promise<void>;
  deleteParcel: (id: string) => Promise<void>;

  addCompensationRecord: (c: Omit<CompensationRecord, 'id' | 'pendingAmountInr'>) => Promise<void>;
  updateCompensationRecord: (id: string, updates: Partial<CompensationRecord>) => Promise<void>;

  addAffectedFamily: (f: Omit<AffectedFamily, 'id' | 'familyRefId'>) => Promise<void>;
  updateAffectedFamily: (id: string, updates: Partial<AffectedFamily>) => Promise<void>;
  deleteAffectedFamily: (id: string) => Promise<void>;

  addDocument: (d: Omit<DocumentItem, 'id' | 'uploadedDate' | 'status'>) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;

  updateMilestone: (id: string, updates: Partial<TimelineMilestone>) => Promise<void>;

  markNotificationAsRead: (id: string) => Promise<void>;
  markAllNotificationsAsRead: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User>(mockUsers[0]);
  const [projects, setProjects] = useState<Project[]>(mockProjects);
  const [parcels, setParcels] = useState<LandParcel[]>(mockParcels);
  const [compensationRecords, setCompensationRecords] = useState<CompensationRecord[]>(mockCompensationRecords);
  const [affectedFamilies, setAffectedFamilies] = useState<AffectedFamily[]>(mockAffectedFamilies);
  const [documents, setDocuments] = useState<DocumentItem[]>(mockDocuments);
  const [milestones, setMilestones] = useState<TimelineMilestone[]>(mockTimeline);
  const [notifications, setNotifications] = useState<NotificationItem[]>(mockNotifications);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const { isAuthenticated } = useAuthContext();

  const refreshData = async () => {
    if (!getToken()) return;
    setIsLoading(true);
    setError(null);
    try {
      // Fetch projects from backend REST API
      const projRes = await projectsApi.getProjects();
      if (projRes && projRes.items && projRes.items.length > 0) {
        setProjects(projRes.items);
      }
      // Fetch notifications
      const notifRes = await notificationsApi.getNotifications();
      if (notifRes && notifRes.items) {
        setNotifications(notifRes.items);
      }
    } catch (err: unknown) {
      console.warn('Backend REST API unreachable, operating on local state mode.', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && getToken()) {
      refreshData();
    }
  }, [isAuthenticated]);

  const setCurrentUserRole = (role: UserRole) => {
    setCurrentUser((prev) => ({ ...prev, role }));
  };

  // Project Actions
  const addProject = async (pData: Omit<Project, 'id' | 'landAcquiredHectares' | 'status'>) => {
    try {
      const created = await projectsApi.createProject(pData as Partial<Project>);
      setProjects((prev) => [created, ...prev]);
    } catch {
      const newProj: Project = {
        ...pData,
        id: `prj-${Date.now()}`,
        landAcquiredHectares: 0,
        status: 'ON_TRACK',
      };
      setProjects((prev) => [newProj, ...prev]);
    }
  };

  const updateProject = async (id: string, updates: Partial<Project>) => {
    try {
      const updated = await projectsApi.updateProject(id, updates);
      setProjects((prev) => prev.map((p) => (p.id === id ? updated : p)));
    } catch {
      setProjects((prev) => prev.map((p) => (p.id === id ? { ...p, ...updates } : p)));
    }
  };

  const deleteProject = async (id: string) => {
    try {
      await projectsApi.deleteProject(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch {
      setProjects((prev) => prev.filter((p) => p.id !== id));
    }
  };

  const updateProjectStage = async (id: string, newStage: LifecycleStage) => {
    try {
      const updated = await projectsApi.updateProject(id, { currentStage: newStage });
      setProjects((prev) => prev.map((p) => (p.id === id ? updated : p)));
    } catch {
      setProjects((prev) => prev.map((p) => (p.id === id ? { ...p, currentStage: newStage } : p)));
    }
  };

  // Parcel Actions
  const addParcel = async (pData: Omit<LandParcel, 'id' | 'parcelCode'>) => {
    try {
      const created = await parcelsApi.createParcel(pData.projectId, pData as Partial<LandParcel>);
      setParcels((prev) => [created, ...prev]);
      await refreshData();
    } catch {
      const stateCode = pData.state ? pData.state.slice(0, 2).toUpperCase() : 'KA';
      const newP: LandParcel = {
        ...pData,
        id: `pcl-${Date.now()}`,
        parcelCode: `LAMS-${stateCode}-SY-${pData.surveyNumber.replace('/', '-')}`,
      };
      setParcels((prev) => [newP, ...prev]);
    }
  };

  const updateParcel = async (id: string, updates: Partial<LandParcel>) => {
    try {
      const updated = await parcelsApi.updateParcel(id, updates);
      setParcels((prev) => prev.map((p) => (p.id === id ? updated : p)));
      await refreshData();
    } catch {
      setParcels((prev) => prev.map((p) => (p.id === id ? { ...p, ...updates } : p)));
    }
  };

  const deleteParcel = async (id: string) => {
    try {
      await parcelsApi.deleteParcel(id);
      setParcels((prev) => prev.filter((p) => p.id !== id));
      await refreshData();
    } catch {
      setParcels((prev) => prev.filter((p) => p.id !== id));
    }
  };

  // Compensation Actions
  const addCompensationRecord = async (cData: Omit<CompensationRecord, 'id' | 'pendingAmountInr'>) => {
    try {
      const created = await compensationApi.createCompensation(cData.projectId, cData as Partial<CompensationRecord>);
      setCompensationRecords((prev) => [created, ...prev]);
    } catch {
      const pendingAmountInr = Math.max(0, cData.approvedAmountInr - cData.disbursedAmountInr);
      const newComp: CompensationRecord = {
        ...cData,
        id: `cmp-${Date.now()}`,
        pendingAmountInr,
      };
      setCompensationRecords((prev) => [newComp, ...prev]);
    }
  };

  const updateCompensationRecord = async (id: string, updates: Partial<CompensationRecord>) => {
    try {
      const updated = await compensationApi.updateCompensation(id, updates);
      setCompensationRecords((prev) => prev.map((c) => (c.id === id ? updated : c)));
    } catch {
      setCompensationRecords((prev) =>
        prev.map((c) => {
          if (c.id === id) {
            const approved = updates.approvedAmountInr !== undefined ? updates.approvedAmountInr : c.approvedAmountInr;
            const disbursed = updates.disbursedAmountInr !== undefined ? updates.disbursedAmountInr : c.disbursedAmountInr;
            return {
              ...c,
              ...updates,
              pendingAmountInr: Math.max(0, approved - disbursed),
            };
          }
          return c;
        })
      );
    }
  };

  // Family Actions
  const addAffectedFamily = async (fData: Omit<AffectedFamily, 'id' | 'familyRefId'>) => {
    try {
      const created = await familiesApi.createFamily(fData.projectId, fData as Partial<AffectedFamily>);
      setAffectedFamilies((prev) => [created, ...prev]);
    } catch {
      const newFam: AffectedFamily = {
        ...fData,
        id: `fam-${Date.now()}`,
        familyRefId: `FAM-IND-${Math.floor(1000 + Math.random() * 9000)}`,
      };
      setAffectedFamilies((prev) => [newFam, ...prev]);
    }
  };

  const updateAffectedFamily = async (id: string, updates: Partial<AffectedFamily>) => {
    try {
      const updated = await familiesApi.updateFamily(id, updates);
      setAffectedFamilies((prev) => prev.map((f) => (f.id === id ? updated : f)));
    } catch {
      setAffectedFamilies((prev) => prev.map((f) => (f.id === id ? { ...f, ...updates } : f)));
    }
  };

  const deleteAffectedFamily = async (id: string) => {
    try {
      await familiesApi.deleteFamily(id);
      setAffectedFamilies((prev) => prev.filter((f) => f.id !== id));
    } catch {
      setAffectedFamilies((prev) => prev.filter((f) => f.id !== id));
    }
  };

  // Document Actions
  const addDocument = async (dData: Omit<DocumentItem, 'id' | 'uploadedDate' | 'status'>) => {
    const newDoc: DocumentItem = {
      ...dData,
      id: `doc-${Date.now()}`,
      uploadedDate: new Date().toISOString().split('T')[0],
      status: 'Verified',
    };
    setDocuments((prev) => [newDoc, ...prev]);
  };

  const deleteDocument = async (id: string) => {
    try {
      await documentsApi.deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch {
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    }
  };

  // Milestone Actions
  const updateMilestone = async (id: string, updates: Partial<TimelineMilestone>) => {
    try {
      const updated = await milestonesApi.updateMilestone(id, updates);
      setMilestones((prev) => prev.map((m) => (m.id === id ? updated : m)));
    } catch {
      setMilestones((prev) => prev.map((m) => (m.id === id ? { ...m, ...updates } : m)));
    }
  };

  const markNotificationAsRead = async (id: string) => {
    try {
      await notificationsApi.markRead(id);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, isRead: true } : n)));
    } catch {
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, isRead: true } : n)));
    }
  };

  const markAllNotificationsAsRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
    } catch {
      setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
    }
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        setCurrentUserRole,
        projects,
        parcels,
        compensationRecords,
        affectedFamilies,
        documents,
        milestones,
        notifications,
        isLoading,
        error,
        refreshData,
        addProject,
        updateProject,
        deleteProject,
        updateProjectStage,
        addParcel,
        updateParcel,
        deleteParcel,
        addCompensationRecord,
        updateCompensationRecord,
        addAffectedFamily,
        updateAffectedFamily,
        deleteAffectedFamily,
        addDocument,
        deleteDocument,
        updateMilestone,
        markNotificationAsRead,
        markAllNotificationsAsRead,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
