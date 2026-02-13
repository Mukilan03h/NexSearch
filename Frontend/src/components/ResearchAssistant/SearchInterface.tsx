import { useState } from 'react';
import { Search, Loader2, Sparkles } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

interface SearchInterfaceProps {
  onSearch: (query: string, maxPapers: number) => void;
  isLoading: boolean;
  recentSearches: string[];
}

export function SearchInterface({ onSearch, isLoading, recentSearches }: SearchInterfaceProps) {
  const [query, setQuery] = useState('');
  const [maxPapers, setMaxPapers] = useState([5]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim(), maxPapers[0]);
    }
  };

  const exampleQueries = [
    'transformer attention',
    'diffusion models',
    'reinforcement learning',
    'graph neural networks',
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-4 md:space-y-6">
      <div className="text-center space-y-2 md:space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-primary/10 to-primary/5 border border-primary/20">
          <Sparkles className="w-3.5 h-3.5 text-primary" />
          <span className="text-xs md:text-sm font-medium text-primary">AI-Powered Research</span>
        </div>
        <h2 className="text-xl md:text-3xl font-bold text-foreground">What would you like to research?</h2>
        <p className="text-sm md:text-base text-muted-foreground px-4">Enter a topic and let AI analyze recent papers for you</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Card className="p-4 md:p-6 space-y-4 bg-card/50 backdrop-blur">
          <div className="relative">
            <Search className="absolute left-3 md:left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 md:w-5 md:h-5 text-muted-foreground" />
            <Input
              placeholder="e.g., transformer attention mechanisms"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10 md:pl-12 h-12 md:h-14 text-base"
              disabled={isLoading}
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-foreground">Maximum Papers</label>
              <Badge variant="secondary" className="font-mono">
                {maxPapers[0]}
              </Badge>
            </div>
            <Slider
              value={maxPapers}
              onValueChange={setMaxPapers}
              min={1}
              max={10}
              step={1}
              disabled={isLoading}
              className="cursor-pointer"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>1</span>
              <span>10</span>
            </div>
          </div>

          <Button
            type="submit"
            size="lg"
            disabled={!query.trim() || isLoading}
            className="w-full h-11 md:h-12 text-sm md:text-base"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Start Research
              </>
            )}
          </Button>
        </Card>
      </form>

      {recentSearches.length > 0 ? (
        <div className="space-y-2">
          <h3 className="text-xs md:text-sm font-medium text-muted-foreground px-2">Recent Searches</h3>
          <div className="flex flex-wrap gap-1.5 md:gap-2">
            {recentSearches.slice(0, 5).map((search, idx) => (
              <Badge
                key={idx}
                variant="outline"
                className="cursor-pointer hover:bg-accent text-xs md:text-sm"
                onClick={() => !isLoading && setQuery(search)}
              >
                {search}
              </Badge>
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <h3 className="text-xs md:text-sm font-medium text-muted-foreground px-2 hidden md:block">Example Queries</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {exampleQueries.map((example, idx) => (
              <Card
                key={idx}
                className="p-3 cursor-pointer hover:bg-accent/50 hover:border-primary/50 transition-all"
                onClick={() => !isLoading && setQuery(example)}
              >
                <p className="text-xs md:text-sm text-foreground/80 truncate">{example}</p>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
