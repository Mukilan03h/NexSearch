import { ResearchQuery, ResearchReport, ApiHealthResponse, ReportSummary } from '@/types/research';

// Use relative paths - Nginx will proxy to backend
// Use env var or default to empty string for relative URLs (goes through Nginx proxy)
const BASE_URL = import.meta.env.VITE_API_URL || '';

// Progress callback type
export type ProgressCallback = (data: {
  status: string;
  message: string;
  papers_found?: number;
  papers_analyzed?: number;
  themes_count?: number;
  report_id?: string;
  query?: string;
  themes?: any[];
  citations?: string[];
  markdown_report?: string;
  minio_url?: string;
}) => void;

export const api = {
  async health(): Promise<ApiHealthResponse> {
    const response = await fetch(`${BASE_URL}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  },

  async submitResearch(query: ResearchQuery): Promise<ResearchReport> {
    const response = await fetch(`${BASE_URL}/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(query),
    });
    if (!response.ok) throw new Error('Research submission failed');
    return response.json();
  },

  // Streaming version with progress callback
  async submitResearchStream(query: ResearchQuery, onProgress: ProgressCallback): Promise<ResearchReport> {
    const response = await fetch(`${BASE_URL}/research/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(query),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Research failed' }));
      throw new Error(error.detail || 'Research submission failed');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    if (!reader) {
      throw new Error('No response body');
    }

    let finalReport: ResearchReport | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            onProgress(data);

            if (data.status === 'complete') {
              finalReport = {
                report_id: data.report_id || '',
                query: data.query || query.query,
                papers_analyzed: data.papers_analyzed || 0,
                themes: data.themes || [],
                citations: data.citations || [],
                markdown_report: data.markdown_report || '',
                minio_url: data.minio_url,
              };
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }
    }

    if (!finalReport) {
      throw new Error('Research did not complete');
    }

    return finalReport;
  },

  async getReports(): Promise<ReportSummary[]> {
    const response = await fetch(`${BASE_URL}/reports`);
    if (!response.ok) throw new Error('Failed to fetch reports');
    return response.json();
  },

  async getReport(reportId: string): Promise<ResearchReport> {
    const response = await fetch(`${BASE_URL}/reports/${reportId}`);
    if (!response.ok) throw new Error('Failed to fetch report');
    return response.json();
  },

  async deleteReport(reportId: string): Promise<void> {
    const response = await fetch(`${BASE_URL}/reports/${reportId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete report');
  },
};
