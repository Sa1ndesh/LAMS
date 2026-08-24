import React from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Bell, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';

export const NotificationsTab: React.FC = () => {
  const notifications = [
    {
      id: 'n-1',
      title: 'Gazette Notification 20A Published',
      message: 'Preliminary notification section 11 issued by District Magistrate for Hoskote taluk.',
      type: 'STAGE_CHANGE',
      date: '2026-08-10',
      isRead: false,
    },
    {
      id: 'n-2',
      title: 'Compensation Disbursement Pending for 3 Parcels',
      message: '₹ 68,000,000 pending direct bank transfer approval for Survey #108/C.',
      type: 'COMPENSATION_PENDING',
      date: '2026-08-18',
      isRead: true,
    },
  ];

  return (
    <div className="space-y-4">
      {notifications.map((n) => (
        <Card key={n.id} className={!n.isRead ? 'border-l-4 border-l-lams-secondary bg-blue-50/20' : ''}>
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-50 text-lams-secondary rounded-xl shrink-0">
              <Bell className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-sm text-lams-primary">{n.title}</h4>
                <span className="text-[11px] text-lams-muted flex items-center gap-1">
                  <Clock className="h-3 w-3" /> {n.date}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">{n.message}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};

