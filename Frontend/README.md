# AI Research Assistant - Frontend

Modern React-based user interface for the AI Research Assistant. Provides an intuitive web interface for conducting AI-powered research with real-time progress tracking, report history, and export capabilities.

## Overview

The frontend offers a clean, responsive interface for:
- Submitting research queries
- Monitoring research progress in real-time
- Viewing generated research reports with themes and citations
- Browsing and managing past research history
- Exporting reports in multiple formats (Markdown, PDF, Word)

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui, Radix UI primitives
- **Icons**: Lucide React
- **Notifications**: Sonner
- **State Management**: React hooks (useState, useEffect)
- **HTTP Client**: Native fetch API
- **Markdown Rendering**: react-markdown + remark-gfm
- **Production Server**: Nginx

## Project Structure

```
src/
├── components/
│   ├── ui/                    # shadcn/ui components
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── collapsible.tsx
│   │   ├── input.tsx
│   │   ├── progress.tsx
│   │   ├── scroll-area.tsx
│   │   ├── separator.tsx
│   │   ├── tabs.tsx
│   │   └── toast.tsx
│   └── ResearchAssistant/     # Feature components
│       ├── LoadingSkeleton.tsx
│       ├── PastReportsSidebar.tsx
│       ├── ResultsDisplay.tsx
│       ├── SearchInterface.tsx
│       └── TopBar.tsx
├── hooks/                     # Custom React hooks
├── lib/
│   ├── api.ts                # Backend API client
│   └── utils.ts              # Utility functions
├── types/
│   └── research.ts           # TypeScript type definitions
├── App.tsx                   # Main application component
├── App.css                   # Global styles
├── index.css                 # Tailwind imports
└── main.tsx                  # Application entry point
```

## Key Components

### App.tsx
Main application component that orchestrates:
- Research state management
- Report history loading from PostgreSQL
- Search execution with streaming progress
- Sidebar navigation for past reports

### SearchInterface.tsx
Primary search input component with:
- Query input field
- Paper count slider (5-50 papers)
- Recent searches display
- Submit button with loading state

### ResultsDisplay.tsx
Multi-tab report viewer featuring:
- **Overview Tab**: Research themes with relevance scores, citations list
- **Full Report Tab**: Rendered markdown report
- **Papers Tab**: Individual paper cards with PDF/external links
- Export buttons (MD, PDF, Word)

### PastReportsSidebar.tsx
History sidebar with:
- Searchable report list
- Report metadata (papers count, timestamp)
- Delete functionality
- Selection highlighting

## API Integration

The frontend communicates with the backend via REST API:

```typescript
// lib/api.ts
const BASE_URL = ''  // Relative URLs through Nginx proxy

api.health()              // GET /health
api.submitResearchStream() // POST /research/stream (SSE)
api.getReports()          // GET /reports
api.getReport(id)         // GET /reports/{id}
api.deleteReport(id)    // DELETE /reports/{id}
```

### Streaming Research
Research queries use Server-Sent Events (SSE) for real-time progress:

```typescript
const response = await fetch(`${BASE_URL}/research/stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query, max_papers }),
});

const reader = response.body?.getReader();
// Parse SSE data: status, message, papers_count, themes, etc.
```

## Development

### Prerequisites
- Node.js 20+
- npm or yarn

### Local Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker Development

The frontend is containerized with Nginx for production:

```bash
# From backend directory (contains main docker-compose)
cd ../backend
docker-compose up -d frontend
```

### Environment Variables

```env
# .env
VITE_API_URL=              # Optional: override API base URL
```

Default behavior uses relative URLs (proxied through Nginx).

## Component Details

### ResultsDisplay Export
Export functionality downloads reports directly from backend:

```typescript
const exportAs = (format: 'md' | 'pdf' | 'docx') => {
  const exportUrl = `http://localhost:8000/reports/${reportId}/export/${format}`;
  // Creates temporary anchor element to trigger download
};
```

### Paper Links
Two actions per paper:
- **PDF Button**: Opens direct PDF (`arxiv.org/pdf/...`)
- **External Link**: Opens abstract page (`arxiv.org/abs/...`)

### Theme Display
Themes show:
- Name and description
- Relevance score (0-100% progress bar)
- Expandable paper list per theme

## Styling

Uses Tailwind CSS with custom configuration:

```javascript
// tailwind.config.js
{
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: '#6366f1', foreground: '#ffffff' },
        // ...
      }
    }
  }
}
```

## Type Definitions

```typescript
// types/research.ts
interface ResearchReport {
  report_id: string;
  query: string;
  papers_analyzed: number;
  themes: Theme[];
  citations: string[];
  markdown_report: string;
  minio_url?: string;
  timestamp?: string;
}

interface Theme {
  name: string;
  description?: string;
  relevance_score: number;
  papers?: Paper[];
}

interface Paper {
  title: string;
  authors: string[];
  abstract?: string;
  arxiv_link?: string;
  pdf_url?: string;
}
```

## Building for Production

```bash
npm run build
```

Output goes to `dist/` directory, served by Nginx in production.

## Docker Production

The production container:
1. Builds React app with Node.js
2. Copies build to Nginx image
3. Uses custom nginx.conf for API proxying

Key Nginx configuration:
```nginx
location / {
    try_files $uri $uri/ /index.html;  # SPA routing
}

location /reports {
    proxy_pass http://app:8000/reports;  # API proxy
}
```

## License

MIT License
