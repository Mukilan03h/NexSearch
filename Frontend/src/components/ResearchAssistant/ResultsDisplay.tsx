import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ExternalLink, Copy, Check, ChevronDown, Download, FileText, File } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ResearchReport, Theme } from '@/types/research';
import { toast } from 'sonner';

interface ResultsDisplayProps {
  report: ResearchReport;
}

// Parse citation to extract paper info
function parseCitation(citation: string): { title: string; authors: string; year: string; url: string } {
  try {
    // Format: [1] Authors (Year). "Title". Source. URL
    const match = citation.match(/\[(\d+)\]\s*(.+?)\s*\((\d{4})\)\.\s*"(.+?)"\.\s*(.+?)\.\s*(http[^\s]+)/);
    if (match) {
      return {
        authors: match[2].trim(),
        year: match[3].trim(),
        title: match[4].trim(),
        url: match[6].trim(),
      };
    }
    // Fallback: try to find URL
    const urlMatch = citation.match(/(http[^\s]+)/);
    return {
      title: citation.slice(0, 50) + '...',
      authors: 'Unknown',
      year: '',
      url: urlMatch ? urlMatch[1] : '',
    };
  } catch {
    return {
      title: citation.slice(0, 50) + '...',
      authors: 'Unknown',
      year: '',
      url: '',
    };
  }
}

export function ResultsDisplay({ report }: ResultsDisplayProps) {
  const [copiedCitation, setCopiedCitation] = useState<number | null>(null);

  const copyToClipboard = async (text: string, index: number) => {
    await navigator.clipboard.writeText(text);
    setCopiedCitation(index);
    toast.success('Copied to clipboard!');
    setTimeout(() => setCopiedCitation(null), 2000);
  };

  // Get papers from citations
  const getPapersFromCitations = () => {
    if (!report.citations || report.citations.length === 0) return [];
    return report.citations.map((citation) => {
      const parsed = parseCitation(citation);
      return {
        title: parsed.title,
        authors: parsed.authors.split(',').map((a: string) => a.trim()),
        abstract: '',
        arxiv_link: parsed.url,
      };
    });
  };

  // Get papers from themes or use citations
  const getPaperInfo = (theme: Theme | undefined) => {
    if (!theme) return [];
    if (theme.papers && theme.papers.length > 0) {
      return theme.papers;
    }
    return [];
  };

  const papersFromThemes = (report.themes || []).flatMap(getPaperInfo);
  const papersFromCitations = getPapersFromCitations();
  const allPapers = papersFromThemes.length > 0 ? papersFromThemes : papersFromCitations;

  // Export based on format (MD, PDF, DOCX)
  const exportAs = (format: 'md' | 'pdf' | 'docx') => {
    const reportId = report.report_id || report.id;
    if (!reportId) {
      toast.error('Report ID missing. Cannot export.');
      return;
    }

    // Construct backend export URL
    const exportUrl = `http://localhost:8000/reports/${reportId}/export/${format}`;

    // Create a temporary link to trigger download
    const link = document.createElement('a');
    link.href = exportUrl;
    link.setAttribute('download', ''); // Ensure browser treats it as a download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    toast.success(`Exporting as ${format.toUpperCase()}...`);
  };

  // Copy all citations to clipboard
  const copyAllCitations = async () => {
    if (!report.citations || report.citations.length === 0) {
      toast.error('No citations to copy');
      return;
    }
    const citationsText = report.citations.join('\n\n');
    await navigator.clipboard.writeText(citationsText);
    toast.success(`Copied ${report.citations.length} citations`);
  };

  // Download paper (Direct PDF link if available)
  const downloadPaper = (paper: { title: string; arxiv_link?: string; pdf_url?: string }) => {
    let link = paper.pdf_url || paper.arxiv_link;
    if (link) {
      // If it's an arXiv abstract link, convert to direct PDF link
      if (link.includes('arxiv.org/abs/')) {
        link = link.replace('arxiv.org/abs/', 'arxiv.org/pdf/');
      }
      window.open(link, '_blank');
    } else {
      toast.error('No link available for this paper');
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-foreground">{report.query || report.query_text}</h2>
            <div className="flex items-center gap-3 mt-2">
              <Badge variant="secondary" className="gap-1">
                {report.papers_analyzed || report.papers_count || allPapers.length || 0} papers analyzed
              </Badge>
              <Badge variant="outline" className="gap-1 font-mono">
                ID: {(report.report_id || report.id || '').slice(0, 8)}
              </Badge>
            </div>
          </div>
          <div className="flex gap-2 shrink-0">
            <div className="flex bg-muted rounded-md p-1">
              <Button
                variant="ghost"
                className="h-8 text-xs gap-1 px-2"
                onClick={() => exportAs('md')}
                title="Export as Markdown"
              >
                <Download className="w-3 h-3" />
                MD
              </Button>
              <Separator orientation="vertical" className="h-4 my-auto mx-1" />
              <Button
                variant="ghost"
                className="h-8 text-xs gap-1 px-2"
                onClick={() => exportAs('pdf')}
                title="Export as PDF"
              >
                <FileText className="w-3 h-3" />
                PDF
              </Button>
              <Separator orientation="vertical" className="h-4 my-auto mx-1" />
              <Button
                variant="ghost"
                className="h-8 text-xs gap-1 px-2"
                onClick={() => exportAs('docx')}
                title="Export as Word"
              >
                <File className="w-3 h-3" />
                Word
              </Button>
            </div>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="report">Full Report</TabsTrigger>
          <TabsTrigger value="papers">Papers</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          {(report.themes || []).length > 0 ? (
            <Card className="bg-gradient-to-br from-primary/5 to-primary/5 border-primary/20">
              <CardHeader>
                <CardTitle>Research Themes</CardTitle>
                <CardDescription>
                  Key themes identified across {report.papers_analyzed || report.papers_count || 0} papers
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {(report.themes || []).map((theme, idx) => (
                  <Collapsible key={idx}>
                    <Card className="overflow-hidden">
                      <CollapsibleTrigger className="w-full">
                        <CardHeader className="cursor-pointer hover:bg-accent/50 transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="flex-1 text-left">
                              <CardTitle className="text-lg">{theme.name}</CardTitle>
                              {theme.description && (
                                <p className="text-sm text-muted-foreground mt-1">{theme.description}</p>
                              )}
                              <div className="flex items-center gap-3 mt-2">
                                <Progress value={(theme.relevance_score || 0) * 100} className="flex-1 h-2" />
                                <span className="text-sm font-medium text-muted-foreground">
                                  {Math.round((theme.relevance_score || 0) * 100)}%
                                </span>
                              </div>
                            </div>
                            <ChevronDown className="w-5 h-5 text-muted-foreground ml-4" />
                          </div>
                        </CardHeader>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <CardContent className="pt-0">
                          <Separator className="mb-4" />
                          <div className="space-y-3">
                            {getPaperInfo(theme).map((paper, paperIdx) => (
                              <div key={paperIdx} className="p-3 rounded-lg bg-muted/50 space-y-2">
                                <p className="font-medium text-sm">{paper.title}</p>
                                <p className="text-xs text-muted-foreground">
                                  {paper.authors?.join(', ') || 'Unknown authors'}
                                </p>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </CollapsibleContent>
                    </Card>
                  </Collapsible>
                ))}
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Citations</CardTitle>
                  <CardDescription>
                    {(report.citations || []).length} citation{(report.citations?.length || 0) !== 1 ? 's' : ''} ready to use
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={copyAllCitations}>
                  <Copy className="w-4 h-4 mr-1" />
                  Copy All
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {(report.citations || []).map((citation, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors group"
                >
                  <div className="flex-1 font-mono text-xs text-foreground/80 break-all">
                    {citation}
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                    onClick={() => copyToClipboard(citation, idx)}
                  >
                    {copiedCitation === idx ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="report" className="mt-6">
          <Card>
            <CardContent className="pt-6">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {report.markdown_report || '*No report generated*'}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="papers" className="mt-6">
          <div className="grid gap-4">
            {allPapers.map((paper, idx) => (
              <Card key={idx} className="hover:shadow-lg transition-all hover:scale-[1.01]">
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <CardTitle className="text-lg leading-tight mb-2">
                        {paper.title}
                      </CardTitle>
                      <CardDescription className="text-sm">
                        {paper.authors?.join(', ') || 'Unknown authors'}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      {paper.arxiv_link && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => downloadPaper(paper)}
                            title="Download Paper"
                          >
                            <File className="w-4 h-4 mr-1" />
                            PDF
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            asChild
                            className="shrink-0"
                          >
                            <a href={paper.arxiv_link} target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
