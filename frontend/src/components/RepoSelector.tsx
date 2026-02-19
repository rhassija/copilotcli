/**
 * Repository Selector Component
 * 
 * Provides:
 * - Searchable repository list
 * - Pagination controls
 * - Repository filtering by visibility
 * - Repository selection
 * 
 * Implements: T095-T096
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { apiService } from '../services/api';

export interface Repository {
  id: number;
  node_id: string;
  name: string;
  full_name: string;
  owner: {
    login: string;
    id: number;
    avatar_url: string;
    type: string;
  };
  private: boolean;
  description: string | null;
  html_url: string;
  default_branch: string;
  stargazers_count: number;
  watchers_count: number;
  forks_count: number;
  open_issues_count: number;
  created_at: string;
  updated_at: string;
  language: string | null;
  visibility: string;
}

export interface RepoSelectorProps {
  onSelect: (repo: Repository) => void;
  selectedRepo: Repository | null;
}

export function RepoSelector({ onSelect, selectedRepo }: RepoSelectorProps) {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination and filters
  const [page, setPage] = useState(1);
  const [perPage] = useState(10);
  const [hasNext, setHasNext] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [visibility, setVisibility] = useState<string>('all');
  const [sort, setSort] = useState('updated');
  
  // Track if we're programmatically resetting page to prevent double-fetch
  const isResettingPage = useRef(false);
  
  /**
   * Reset to page 1 when filters change
   */
  useEffect(() => {
    if (page !== 1) {
      isResettingPage.current = true;
      setPage(1);
    }
  }, [searchTerm, visibility, sort]); // Don't include 'page' in deps
  
  /**
   * Fetch repositories from API
   */
  useEffect(() => {
    // Skip fetch if we just reset the page (will fetch on next render with page=1)
    if (isResettingPage.current) {
      isResettingPage.current = false;
      return;
    }
    
    const fetchRepositories = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await apiService.get<{
          repositories: Repository[];
          total_count: number;
          page: number;
          per_page: number;
          has_next: boolean;
        }>('/api/v1/repos', {
          params: {
            visibility: visibility === 'all' ? undefined : visibility,
            sort,
            search: searchTerm || undefined,
            page,
            per_page: perPage,
            use_cache: true,
          },
        });
        
        setRepos(response.repositories);
        setHasNext(response.has_next);
      } catch (err: any) {
        console.error('Failed to fetch repositories:', err);
        setError(err.response?.data?.error?.message || err.message || 'Failed to load repositories');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchRepositories();
  }, [page, perPage, searchTerm, visibility, sort]);
  
  /**
   * Handle repository selection
   */
  const handleSelect = (repo: Repository) => {
    onSelect(repo);
  };
  
  /**
   * Format date for display
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };
  
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          📚 Select Repository
        </h2>
        <button
          onClick={fetchRepositories}
          disabled={isLoading}
          className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md transition-colors disabled:opacity-50"
        >
          {isLoading ? '⟳' : '↻'} Refresh
        </button>
      </div>
      
      {/* Search and Filter Bar */}
      <div className="space-y-3">
        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            placeholder="🔍 Search repositories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
        </div>
        
        {/* Filters */}
        <div className="flex gap-3">
          <select
            value={visibility}
            onChange={(e) => setVisibility(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Repositories</option>
            <option value="public">Public</option>
            <option value="private">Private</option>
          </select>
          
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="updated">Recently Updated</option>
            <option value="created">Recently Created</option>
            <option value="pushed">Recently Pushed</option>
            <option value="full_name">Name</option>
          </select>
        </div>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}
      
      {/* Loading State */}
      {isLoading && repos.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600 dark:text-gray-400">Loading repositories...</span>
        </div>
      )}
      
      {/* Repository List */}
      {!isLoading && repos.length === 0 && !error && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">No repositories found</p>
        </div>
      )}
      
      {repos.length > 0 && (
        <div className="space-y-2">
          {repos.map((repo) => (
            <button
              key={repo.id}
              onClick={() => handleSelect(repo)}
              className={`w-full text-left p-4 rounded-lg border transition-all ${
                selectedRepo?.id === repo.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 bg-white dark:bg-gray-800'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">📦</span>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {repo.full_name}
                    </h3>
                    {repo.private && (
                      <span className="px-2 py-0.5 text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 rounded">
                        Private
                      </span>
                    )}
                  </div>
                  {repo.description && (
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {repo.description}
                    </p>
                  )}
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                    {repo.language && (
                      <span className="flex items-center gap-1">
                        <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                        {repo.language}
                      </span>
                    )}
                    <span>⭐ {repo.stargazers_count}</span>
                    <span>🔱 {repo.forks_count}</span>
                    <span>Updated {formatDate(repo.updated_at)}</span>
                  </div>
                </div>
                {selectedRepo?.id === repo.id && (
                  <span className="text-blue-600 dark:text-blue-400 text-xl">✓</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
      
      {/* Pagination */}
      {repos.length > 0 && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
            className="px-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>
          
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {page}
          </span>
          
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!hasNext || isLoading}
            className="px-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
