/**
 * Feature List Component
 * 
 * Provides:
 * - Display list of features for a repository
 * - Feature status indicators
 * - Document links
 * - Refresh functionality
 * 
 * Implements: T100 (part of feature management)
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { apiService } from '../services/api';
import type { Feature } from './FeatureCreator';
import type { Repository } from './RepoSelector';

export interface FeatureListProps {
  repository: Repository;
  onRefresh?: () => void;
}

export function FeatureList({ repository, onRefresh }: FeatureListProps) {
  const [features, setFeatures] = useState<Feature[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  /**
   * Fetch features for repository
   */
  const fetchFeatures = useCallback(async () => {
    if (!repository) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const [owner, repo] = repository.full_name.split('/');
      const response = await apiService.get<{
        features: Feature[];
        repository: string;
        total_count: number;
      }>(`/api/v1/repos/${owner}/${repo}/features`);
      
      setFeatures(response.features);
    } catch (err: any) {
      console.error('Failed to fetch features:', err);
      setError(err.response?.data?.error?.message || err.message || 'Failed to load features');
    } finally {
      setIsLoading(false);
    }
  }, [repository]);
  
  // Fetch on mount and when repository changes
  useEffect(() => {
    fetchFeatures();
  }, [fetchFeatures]);
  
  /**
   * Handle refresh
   */
  const handleRefresh = () => {
    fetchFeatures();
    onRefresh?.();
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
  
  /**
   * Get status badge color
   */
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400';
      case 'in_progress':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400';
      case 'ready_for_review':
        return 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-400';
      case 'completed':
        return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-400';
      case 'initializing':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400';
      default:
        return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-400';
    }
  };
  
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          🌿 Active Features
        </h3>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md transition-colors disabled:opacity-50"
        >
          {isLoading ? '⟳' : '↻'} Refresh
        </button>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}
      
      {/* Loading State */}
      {isLoading && features.length === 0 && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600 dark:text-gray-400">Loading features...</span>
        </div>
      )}
      
      {/* Empty State */}
      {!isLoading && features.length === 0 && !error && (
        <div className="text-center py-8 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400">No features yet</p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
            Click "+ Create Feature" to get started
          </p>
        </div>
      )}
      
      {/* Feature List */}
      {features.length > 0 && (
        <div className="space-y-3">
          {features.map((feature) => (
            <div
              key={feature.feature_id}
              className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {feature.branch_name}
                    </h4>
                    <span className={`px-2 py-0.5 text-xs rounded ${getStatusColor(feature.status)}`}>
                      {feature.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    "{feature.title}"
                  </p>
                  
                  {/* Documents */}
                  {(feature.spec_path || feature.plan_path || feature.task_path) && (
                    <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                      {feature.spec_path && (
                        <span className="flex items-center gap-1">
                          📄 spec.md
                        </span>
                      )}
                      {feature.plan_path && (
                        <span className="flex items-center gap-1">
                          📋 plan.md
                        </span>
                      )}
                      {feature.task_path && (
                        <span className="flex items-center gap-1">
                          ✅ tasks.md
                        </span>
                      )}
                    </div>
                  )}
                  
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                    Created {formatDate(feature.created_at)} • Base: {feature.base_branch}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
