import React from 'react';
import { Badge } from './Badge';
import { CheckCircle2, Clock, AlertTriangle, AlertCircle } from 'lucide-react';
import { ProjectStatus, LifecycleStage } from '../../types';

interface StatusBadgeProps {
  status: ProjectStatus | LifecycleStage | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  switch (status) {
    case 'ON_TRACK':
    case 'Completed':
    case 'Acquired':
    case 'Disbursed':
    case 'Resettled':
      return (
        <Badge variant="success" size={size} icon={<CheckCircle2 className="h-3 w-3" />}>
          {status === 'ON_TRACK' ? 'On Track' : status}
        </Badge>
      );
    case 'DELAYED':
    case 'Pending':
    case 'Verification':
    case 'Survey':
      return (
        <Badge variant="warning" size={size} icon={<Clock className="h-3 w-3" />}>
          {status === 'DELAYED' ? 'Delayed' : status}
        </Badge>
      );
    case 'CRITICAL':
      return (
        <Badge variant="danger" size={size} icon={<AlertTriangle className="h-3 w-3" />}>
          Critical Risk
        </Badge>
      );
    case 'Notification':
    case 'Award':
    case 'Compensation':
    case 'Possession':
    case 'Rehabilitation & Resettlement':
      return (
        <Badge variant="info" size={size} icon={<AlertCircle className="h-3 w-3" />}>
          {status}
        </Badge>
      );
    default:
      return <Badge variant="neutral" size={size}>{status}</Badge>;
  }
};

