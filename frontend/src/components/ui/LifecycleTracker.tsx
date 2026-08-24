import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { LifecycleStage } from '../../types';

interface LifecycleTrackerProps {
  currentStage: LifecycleStage;
  onStageSelect?: (stage: LifecycleStage) => void;
}

export const LIFECYCLE_STAGES: LifecycleStage[] = [
  'Proposal',
  'Verification',
  'Survey',
  'Notification',
  'Award',
  'Compensation',
  'Possession',
  'Rehabilitation & Resettlement',
  'Completed',
];

export const LifecycleTracker: React.FC<LifecycleTrackerProps> = ({
  currentStage,
  onStageSelect,
}) => {
  const currentStageIndex = LIFECYCLE_STAGES.indexOf(currentStage);

  return (
    <div className="w-full bg-white p-4 sm:p-6 rounded-xl border border-lams-border shadow-card overflow-x-auto">
      <div className="flex items-center justify-between min-w-[800px]">
        {LIFECYCLE_STAGES.map((stage, idx) => {
          const isCompleted = idx < currentStageIndex;
          const isCurrent = idx === currentStageIndex;

          return (
            <React.Fragment key={stage}>
              <div
                onClick={() => onStageSelect?.(stage)}
                className={`flex flex-col items-center flex-1 text-center group cursor-pointer transition-transform ${
                  onStageSelect ? 'hover:scale-105' : ''
                }`}
              >
                <div
                  className={`h-9 w-9 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    isCompleted
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : isCurrent
                      ? 'bg-lams-secondary text-white ring-4 ring-blue-100 shadow-md scale-110'
                      : 'bg-slate-100 text-slate-400 border border-slate-200'
                  }`}
                >
                  {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : idx + 1}
                </div>

                <span
                  className={`text-[11px] font-semibold mt-2.5 max-w-[90px] leading-tight ${
                    isCurrent
                      ? 'text-lams-secondary font-bold'
                      : isCompleted
                      ? 'text-emerald-700'
                      : 'text-slate-400'
                  }`}
                >
                  {stage}
                </span>
              </div>

              {idx < LIFECYCLE_STAGES.length - 1 && (
                <div className="flex-1 px-1">
                  <div
                    className={`h-1 rounded-full transition-colors ${
                      idx < currentStageIndex ? 'bg-emerald-600' : 'bg-slate-200'
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

