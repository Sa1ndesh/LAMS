import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { mockProjects } from '../data/mockData';
import { ArrowLeft, CheckCircle2, MapPin, Building, Calendar, IndianRupee, Layers } from 'lucide-react';

export const ProjectOverview: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const project = mockProjects.find((p) => p.id === id) || mockProjects[0];

  const stages = [
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

  const currentStageIndex = stages.indexOf(project.currentStage);

  return (
    <PageContainer
      title={project.name}
      description={`Project Code: ${project.projectCode} • ${project.district}, ${project.state}`}
      actions={
        <Button
          variant="outline"
          icon={<ArrowLeft className="h-4 w-4" />}
          onClick={() => navigate('/projects')}
        >
          Back to Directory
        </Button>
      }
    >
      {/* 9-Stage Lifecycle Tracker Bar */}
      <Card title="Land Acquisition Lifecycle Progress" className="mb-6">
        <div className="overflow-x-auto py-2">
          <div className="flex items-center min-w-[750px]">
            {stages.map((stage, idx) => {
              const isCompleted = idx < currentStageIndex;
              const isCurrent = idx === currentStageIndex;
              return (
                <React.Fragment key={stage}>
                  <div className="flex flex-col items-center flex-1 text-center">
                    <div
                      className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                        isCompleted
                          ? 'bg-emerald-600 text-white'
                          : isCurrent
                          ? 'bg-lams-secondary text-white ring-4 ring-blue-100'
                          : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : idx + 1}
                    </div>
                    <span
                      className={`text-[11px] font-semibold mt-2 ${
                        isCurrent ? 'text-lams-secondary' : isCompleted ? 'text-emerald-700' : 'text-slate-400'
                      }`}
                    >
                      {stage}
                    </span>
                  </div>
                  {idx < stages.length - 1 && (
                    <div
                      className={`h-1 flex-1 transition-colors ${
                        idx < currentStageIndex ? 'bg-emerald-600' : 'bg-slate-200'
                      }`}
                    ></div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Project Summary" className="md:col-span-2 space-y-4">
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-lams-muted font-medium block">Project Type</span>
              <span className="font-semibold text-lams-dark text-sm flex items-center gap-1.5 mt-0.5">
                <Layers className="h-4 w-4 text-lams-secondary" /> {project.projectType}
              </span>
            </div>
            <div>
              <span className="text-lams-muted font-medium block">Implementing Agency</span>
              <span className="font-semibold text-lams-dark text-sm flex items-center gap-1.5 mt-0.5">
                <Building className="h-4 w-4 text-lams-secondary" /> {project.implementingAgency}
              </span>
            </div>
            <div>
              <span className="text-lams-muted font-medium block">Ministry</span>
              <span className="font-semibold text-lams-dark">{project.ministry}</span>
            </div>
            <div>
              <span className="text-lams-muted font-medium block">Location</span>
              <span className="font-semibold text-lams-dark flex items-center gap-1 mt-0.5">
                <MapPin className="h-3.5 w-3.5 text-lams-muted" /> {project.village}, {project.district}, {project.state}
              </span>
            </div>
            <div>
              <span className="text-lams-muted font-medium block">Proposed Land Area</span>
              <span className="font-semibold text-lams-dark text-sm">{project.landProposedHectares} Hectares</span>
            </div>
            <div>
              <span className="text-lams-muted font-medium block">Acquired Land Area</span>
              <span className="font-semibold text-emerald-700 text-sm">{project.landAcquiredHectares} Hectares</span>
            </div>
          </div>
        </Card>

        <Card title="Financial & Timeline">
          <div className="space-y-4 text-xs">
            <div>
              <span className="text-lams-muted font-medium block">Total Allocated Budget</span>
              <span className="text-lg font-bold text-lams-primary flex items-center gap-1 mt-0.5">
                <IndianRupee className="h-5 w-5" /> {(project.budgetInr / 10000000).toLocaleString('en-IN')} Cr
              </span>
            </div>
            <div className="pt-3 border-t border-lams-border">
              <span className="text-lams-muted font-medium block">Start Date</span>
              <span className="font-semibold text-lams-dark flex items-center gap-1.5 mt-0.5">
                <Calendar className="h-3.5 w-3.5 text-lams-muted" /> {project.startDate}
              </span>
            </div>
            <div>
              <span className="text-lams-muted font-medium block">Target Completion Date</span>
              <span className="font-semibold text-lams-dark flex items-center gap-1.5 mt-0.5">
                <Calendar className="h-3.5 w-3.5 text-lams-muted" /> {project.targetCompletionDate}
              </span>
            </div>
            <div className="pt-3 border-t border-lams-border flex items-center justify-between">
              <span className="text-lams-muted font-medium">Status</span>
              <Badge variant={project.status === 'ON_TRACK' ? 'success' : 'danger'}>
                {project.status}
              </Badge>
            </div>
          </div>
        </Card>
      </div>
    </PageContainer>
  );
};

