import { Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface LoadingSkeletonProps {
  isLoading?: boolean;
  progress?: {
    status: string;
    message: string;
  };
}

// Map status to display values
const getStatusInfo = (status: string, message: string) => {
  switch (status) {
    case 'starting':
      return { label: 'Starting', description: message || 'Initializing research...' };
    case 'planning':
      return { label: 'Planning', description: message || 'Creating search plan...' };
    case 'fetching':
      return { label: 'Fetching', description: message || 'Searching for papers...' };
    case 'fetched':
      return { label: 'Fetched', description: message || 'Papers found, analyzing...' };
    case 'analyzing':
      return { label: 'Analyzing', description: message || 'Analyzing papers and extracting themes...' };
    case 'analyzed':
      return { label: 'Analyzed', description: message || 'Themes extracted, generating report...' };
    case 'writing':
      return { label: 'Writing', description: message || 'Generating research report...' };
    case 'complete':
      return { label: 'Complete', description: message || 'Your report is ready!' };
    case 'error':
      return { label: 'Error', description: message || 'Something went wrong' };
    default:
      return { label: 'Processing', description: message || 'Please wait...' };
  }
};

// Calculate progress percentage
const getProgressPercent = (status: string) => {
  const statusOrder = ['starting', 'planning', 'fetching', 'fetched', 'analyzing', 'analyzed', 'writing', 'complete'];
  const idx = statusOrder.indexOf(status);
  if (idx === -1) return 10;
  return Math.min((idx + 1) * 12, 95);
};

export function LoadingSkeleton({ isLoading = true, progress }: LoadingSkeletonProps) {
  // Don't render if not loading (parent will show results)
  if (!isLoading) {
    return null;
  }

  const statusInfo = getStatusInfo(progress?.status || '', progress?.message || '');
  const progressPercent = getProgressPercent(progress?.status || '');

  return (
    <div className="max-w-2xl mx-auto">
      {/* Main Card */}
      <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
        <CardContent className="pt-8 pb-8">
          <div className="text-center space-y-6">
            {/* Icon */}
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-primary animate-spin" />
              </div>
            </div>

            {/* Title */}
            <div>
              <h2 className="text-2xl font-bold text-foreground">
                {statusInfo.label}
              </h2>
              <p className="text-muted-foreground mt-2">
                {statusInfo.description}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="w-full bg-primary/20 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>{progress?.status || 'starting'}</span>
                <span>{progressPercent}%</span>
              </div>
            </div>

            {/* Current Stage Description */}
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">{statusInfo.description}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stage Indicators */}
      <div className="flex justify-center gap-1 mt-4">
        {['planning', 'fetching', 'analyzing', 'writing', 'complete'].map((stage, index) => {
          const statusOrder = ['starting', 'planning', 'fetching', 'fetched', 'analyzing', 'analyzed', 'writing', 'complete'];
          const currentIdx = statusOrder.indexOf(progress?.status || '');
          const stageIdx = index + 1; // stages after starting
          const isActive = currentIdx >= stageIdx;
          const isCurrent = progress?.status === stage || (stage === 'complete' && progress?.status === 'complete');

          return (
            <div
              key={stage}
              className={`w-3 h-3 rounded-full transition-all ${
                isCurrent ? 'bg-green-500 scale-125' : isActive ? 'bg-primary' : 'bg-muted'
              }`}
              title={stage}
            />
          );
        })}
      </div>
    </div>
  );
}
