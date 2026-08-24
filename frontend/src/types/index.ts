export type UserRole =
  | 'SUPER_ADMIN'
  | 'CENTRAL_MINISTRY'
  | 'STATE_AUTHORITY'
  | 'DISTRICT_ADMIN'
  | 'LAND_ACQUISITION_OFFICER'
  | 'FIELD_OFFICER'
  | 'PROJECT_IMPLEMENTING_AGENCY'
  | 'VIEWER';

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  department?: string;
  state?: string;
  district?: string;
}

export type LifecycleStage =
  | 'Proposal'
  | 'Verification'
  | 'Survey'
  | 'Notification'
  | 'Award'
  | 'Compensation'
  | 'Possession'
  | 'Rehabilitation & Resettlement'
  | 'Completed';

export type ProjectStatus = 'ON_TRACK' | 'DELAYED' | 'CRITICAL' | 'COMPLETED';

export interface Project {
  id: string;
  projectCode: string;
  name: string;
  projectType: string;
  ministry: string;
  implementingAgency: string;
  state: string;
  district: string;
  village: string;
  landProposedHectares: number;
  landAcquiredHectares: number;
  budgetInr: number;
  currentStage: LifecycleStage;
  startDate: string;
  targetCompletionDate: string;
  status: ProjectStatus;
  description?: string;
}

export interface LandParcel {
  id: string;
  parcelCode: string;
  projectId: string;
  surveyNumber: string;
  state: string;
  district: string;
  taluk: string;
  village: string;
  areaHectares: number;
  landType: string;
  ownerName: string;
  acquisitionStatus: 'Proposed' | 'Verified' | 'Surveyed' | 'Notified' | 'Awarded' | 'Acquired';
  compensationStatus: 'Pending' | 'Assessed' | 'Approved' | 'Disbursed';
  possessionStatus: 'Not Taken' | 'Demarcated' | 'Taken';
  latitude: number;
  longitude: number;
}

export interface CompensationRecord {
  id: string;
  parcelId: string;
  projectId: string;
  assessedAmountInr: number;
  approvedAmountInr: number;
  disbursedAmountInr: number;
  pendingAmountInr: number;
  paymentStatus: 'Assessed' | 'Approved' | 'Partially Disbursed' | 'Disbursed' | 'Pending';
  paymentDate?: string;
}

export interface AffectedFamily {
  id: string;
  familyRefId: string;
  projectId: string;
  village: string;
  headOfFamily: string;
  familyMembersCount: number;
  category: 'General' | 'OBC' | 'SC' | 'ST';
  isDisplaced: boolean;
  rrStatus: 'Identified' | 'Eligible' | 'Assistance Disbursed' | 'Resettled' | 'Completed';
}

export interface DocumentItem {
  id: string;
  projectId: string;
  docType: string;
  title: string;
  fileType: string;
  fileSize: string;
  uploadedBy: string;
  uploadedDate: string;
  status: string;
  version?: string;
  description?: string;
  filePath?: string;
  mimeType?: string;
}

export interface TimelineMilestone {
  id: string;
  projectId: string;
  title: string;
  stage: LifecycleStage | string;
  plannedDate: string;
  actualDate?: string;
  status: 'Completed' | 'In Progress' | 'Pending' | 'Delayed';
  delayDays?: number;
}

export interface NotificationItem {
  id: string;
  projectId?: string;
  title: string;
  message: string;
  eventType: 'PROJECT_PROPOSAL' | 'STAGE_CHANGE' | 'PARCEL_ADDED' | 'COMPENSATION_UPDATED' | 'MILESTONE_DELAYED' | 'DOCUMENT_UPLOADED';
  date: string;
  isRead: boolean;
}

export interface NavItemType {
  label: string;
  path: string;
  iconName: string;
  badge?: string | number;
  roles?: UserRole[];
}
