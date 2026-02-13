export interface ResearchQuery {
  query: string;
  max_papers: number;
}

export interface Paper {
  title: string;
  authors: string[];
  abstract: string;
  arxiv_link: string;
  pdf_url?: string;
  relevance_score?: number;
}

export interface Theme {
  name: string;
  description?: string;
  relevance_score: number;
  paper_ids?: string[];
  papers?: Paper[];
}

export interface ResearchReport {
  report_id: string;
  id?: string;
  query: string;
  query_text?: string;
  papers_analyzed: number;
  papers_count?: number;
  themes: Theme[];
  citations: string[];
  markdown_report?: string;
  markdown_content?: string;
  top_papers?: Paper[];
  minio_url?: string;
  timestamp?: string;
  created_at?: string;
}

export interface ReportSummary {
  id: string;
  report_id?: string;
  query_text: string;
  created_at: string;
  papers_count: number;
  themes_count?: number;
  citations_count?: number;
}

export interface ApiHealthResponse {
  status: string;
}
