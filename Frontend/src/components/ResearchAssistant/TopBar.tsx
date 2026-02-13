import { useState, useEffect } from 'react';
import { AlertCircle, Plus } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ThemeToggle } from './ThemeToggle';
import { api } from '@/lib/api';

interface TopBarProps {
  onNewChat?: () => void;
}

export function TopBar({ onNewChat }: TopBarProps) {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.health();
        setIsHealthy(true);
      } catch {
        setIsHealthy(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-16 border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-4 md:px-6">
      <div className="flex items-center gap-2 md:gap-3">
        <img
          src="/nexsearchlogo.png"
          alt="NexSearch"
          className="w-8 h-8 md:w-10 md:h-10 rounded-lg object-contain"
        />
        <div>
          <h1 className="text-lg md:text-xl font-semibold text-foreground">NexSearch</h1>
          <p className="text-xs text-muted-foreground hidden sm:block">AI-Powered Research</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {onNewChat && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="default"
                  size="sm"
                  onClick={onNewChat}
                  className="gap-2"
                >
                  <Plus className="w-4 h-4" />
                  <span className="hidden sm:inline">New Chat</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Start a new research session</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        <ThemeToggle />

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <Badge
                variant={isHealthy === true ? 'default' : isHealthy === false ? 'destructive' : 'secondary'}
                className="gap-1.5"
              >
                {isHealthy === true ? (
                  <>
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="hidden sm:inline">Online</span>
                  </>
                ) : isHealthy === false ? (
                  <>
                    <AlertCircle className="w-3 h-3" />
                    <span className="hidden sm:inline">Offline</span>
                  </>
                ) : (
                  '...'
                )}
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p>{isHealthy === true ? 'Backend API is healthy' : isHealthy === false ? 'Cannot reach backend API' : 'Checking API status...'}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  );
}
