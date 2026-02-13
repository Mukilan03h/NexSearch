import { useState, useEffect, useRef } from 'react';
import { Toaster } from 'sonner';
import { toast } from 'sonner';
import { Menu, X } from 'lucide-react';
import { TopBar } from '@/components/ResearchAssistant/TopBar';
import { PastReportsSidebar } from '@/components/ResearchAssistant/PastReportsSidebar';
import { SearchInterface } from '@/components/ResearchAssistant/SearchInterface';
import { ResultsDisplay } from '@/components/ResearchAssistant/ResultsDisplay';
import { LoadingSkeleton } from '@/components/ResearchAssistant/LoadingSkeleton';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { ResearchReport } from '@/types/research';
import './App.css';

function App() {
  const [reports, setReports] = useState<ResearchReport[]>([]);
  const [currentReport, setCurrentReport] = useState<ResearchReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoadingReports, setIsLoadingReports] = useState(true);
  const [progress, setProgress] = useState<{ status: string; message: string }>({ status: '', message: '' });
  const resultsRef = useRef<HTMLDivElement>(null);

  // Load reports from PostgreSQL API on mount
  useEffect(() => {
    const loadReports = async () => {
      setIsLoadingReports(true);
      try {
        const dbReports = await api.getReports();
        if (dbReports && Array.isArray(dbReports) && dbReports.length > 0) {
          // Transform API response to ResearchReport format
          const transformed = dbReports.map(r => ({
            id: r.id || r.report_id || '',
            report_id: r.id || r.report_id || '',
            query: r.query_text,
            query_text: r.query_text,
            papers_analyzed: r.papers_count || 0,
            papers_count: r.papers_count,
            timestamp: r.created_at,
            created_at: r.created_at,
            themes: [],
            citations: [],
          }));
          setReports(transformed);
        }
      } catch (e) {
        console.error('Failed to load reports from database:', e);
        toast.error('Failed to load past reports', {
          description: 'Could not connect to the server.'
        });
      } finally {
        setIsLoadingReports(false);
      }
    };
    loadReports();
  }, []);


  // Scroll to results when loading starts
  useEffect(() => {
    if (isLoading && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [isLoading]);

  const handleNewChat = () => {
    setCurrentReport(null);
    setSidebarOpen(false);
  };

  const handleDeleteReport = async (reportId: string) => {
    try {
      await api.deleteReport(reportId);
    } catch (e) {
      console.log('API delete failed, removing locally only');
    }
    setReports(prev => prev.filter(r => (r.report_id || r.id) !== reportId));
    if (currentReport && (currentReport.report_id || currentReport.id) === reportId) {
      setCurrentReport(null);
    }
    toast.success('Report deleted');
  };

  const handleSelectReport = async (report: ResearchReport) => {
    const reportId = report.report_id || report.id;
    if (!reportId) {
      setCurrentReport(report);
      return;
    }

    // Check if we already have full report data
    const hasFullData = report.markdown_report || report.markdown_content || (report.themes && report.themes.length > 0) || (report.citations && report.citations.length > 0);

    if (!hasFullData) {
      try {
        const fullReport = await api.getReport(reportId);
        const reportWithFullData = {
          ...fullReport,
          id: fullReport.id || reportId,
          report_id: fullReport.id || reportId,
          query: fullReport.query_text || '',
          papers_analyzed: fullReport.papers_count || 0,
          markdown_report: fullReport.markdown_content || fullReport.markdown_report,
        };
        setCurrentReport(reportWithFullData);

        // Update the cached reports list with full data
        setReports(prev => prev.map(r =>
          (r.report_id || r.id) === reportId
            ? { ...r, ...reportWithFullData }
            : r
        ));
      } catch (e) {
        console.error('Failed to fetch full report:', e);
        setCurrentReport(report);
      }
    } else {
      setCurrentReport(report);
    }

    setSidebarOpen(false);
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // Show toast when report is actually loaded and displayed (only for new searches)
  const [hasNewSearch, setHasNewSearch] = useState(false);
  useEffect(() => {
    if (currentReport && !isLoading && hasNewSearch) {
      const papersCount = currentReport.papers_analyzed || currentReport.papers_count || 0;
      toast.success(`Research completed! Analyzed ${papersCount} papers. Your report is ready below.`, {
        duration: 4000,
      });
      setHasNewSearch(false);
    }
  }, [currentReport, isLoading, hasNewSearch]);

  const handleSearch = async (query: string, maxPapers: number) => {
    setHasNewSearch(true);
    setIsLoading(true);
    setCurrentReport(null);
    setSidebarOpen(false);
    setProgress({ status: 'starting', message: 'Initializing research...' });

    try {
      // Use streaming API with progress callbacks
      const report = await api.submitResearchStream(
        { query, max_papers: maxPapers },
        (data) => {
          setProgress({
            status: data.status,
            message: data.message
          });
        }
      );

      const reportId = report.report_id || report.id || `report_${Date.now()}`;
      const reportWithTimestamp = {
        ...report,
        report_id: reportId,
        id: reportId,
        timestamp: new Date().toISOString()
      };

      setCurrentReport(reportWithTimestamp);
      setReports(prev => [reportWithTimestamp, ...prev]);
      setRecentSearches(prev => {
        const updated = [query, ...prev.filter(q => q !== query)];
        return updated.slice(0, 10);
      });

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (error) {
      console.error('Research failed:', error);
      toast.error('Research failed', {
        description: error instanceof Error ? error.message : 'Could not complete the research. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background text-foreground overflow-hidden">
      <TopBar onNewChat={handleNewChat} />

      <div className="flex-1 flex overflow-hidden">
        {/* Mobile sidebar toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="fixed bottom-4 left-4 z-50 md:hidden h-12 w-12 shadow-lg"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>

        {/* Sidebar */}
        <div className={`
          fixed md:relative z-40 h-full
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          transition-transform duration-200 ease-in-out
        `}>
          <PastReportsSidebar
            reports={reports}
            onSelectReport={handleSelectReport}
            selectedReportId={currentReport?.report_id || currentReport?.id}
            onDeleteReport={handleDeleteReport}
            isLoading={isLoadingReports}
          />
        </div>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          <div className="container max-w-4xl mx-auto p-4 md:p-6 space-y-6 md:space-y-8">
            <SearchInterface
              onSearch={handleSearch}
              isLoading={isLoading}
              recentSearches={recentSearches}
            />

            <div ref={resultsRef}>
              {isLoading && (
                <LoadingSkeleton progress={progress} />
              )}

              {!isLoading && currentReport && (
                <ResultsDisplay report={currentReport} />
              )}

              {!isLoading && !currentReport && reports.length > 0 && (
                <div className="text-center py-8 md:py-12">
                  <p className="text-muted-foreground">Select a report from the sidebar or start a new research</p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
