import { useState } from 'react';
import { Search, FileText, Clock, Trash2, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { ResearchReport } from '@/types/research';
import { getRelativeTime } from '@/lib/utils-date';

interface PastReportsSidebarProps {
  reports: ResearchReport[];
  onSelectReport: (report: ResearchReport) => void;
  selectedReportId?: string;
  onDeleteReport?: (reportId: string) => void;
  isLoading?: boolean;
}

export function PastReportsSidebar({ reports, onSelectReport, selectedReportId, onDeleteReport, isLoading }: PastReportsSidebarProps) {
  const [searchTerm, setSearchTerm] = useState('');

  // Handle both query and query_text field names
  const getQueryText = (report: ResearchReport): string => {
    return report.query || report.query_text || 'Untitled';
  };

  const filteredReports = reports.filter((report) =>
    getQueryText(report).toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="w-[280px] border-r border-border/40 bg-muted/30 flex flex-col h-full">
      <div className="p-4 border-b border-border/40">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 bg-background/50"
          />
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2 mb-3">
                Past Reports ({filteredReports.length})
              </h3>

              {filteredReports.length === 0 ? (
            <div className="text-center py-12 px-4">
              <FileText className="w-12 h-12 mx-auto text-muted-foreground/50 mb-3" />
              <p className="text-sm text-muted-foreground mb-1">
                {searchTerm ? 'No reports found' : 'No reports yet'}
              </p>
              <p className="text-xs text-muted-foreground/70">
                {searchTerm ? 'Try a different search term' : 'Start your first research query'}
              </p>
            </div>
          ) : (
            filteredReports.map((report) => (
              <Card
                key={report.report_id || report.id}
                className={`p-3 cursor-pointer transition-all hover:bg-accent/50 hover:shadow-md group ${
                  selectedReportId === (report.report_id || report.id) ? 'bg-accent border-[#6366f1]' : ''
                }`}
                onClick={() => onSelectReport(report)}
              >
                <div className="space-y-2">
                  <p className="text-sm font-medium line-clamp-2 leading-tight">
                    {getQueryText(report)}
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {report.timestamp ? getRelativeTime(report.timestamp) : report.created_at ? getRelativeTime(report.created_at) : 'Recently'}
                    </div>
                    <div className="flex items-center gap-1">
                      <Badge variant="secondary" className="text-xs">
                        {report.papers_analyzed || report.papers_count || 0} papers
                      </Badge>
                      {onDeleteReport && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteReport(report.report_id || report.id || '');
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-destructive/20 rounded transition-all"
                        >
                          <Trash2 className="w-3 h-3 text-destructive" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
