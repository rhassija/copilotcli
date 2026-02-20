/**
 * Features page - Browse all features across repositories.
 * 
 * Displays list of features with filters and navigation.
 */

'use client';

import { useAuth } from '../../hooks/useAuth';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState, useCallback } from 'react';
import Layout from '../../components/Layout';
import Loading from '../../components/Loading';
import { apiService } from '../../services/api';
import type { Feature } from '../../components/FeatureCreator';

export default function FeaturesPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isMounted, setIsMounted] = useState(false);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [filteredFeatures, setFilteredFeatures] = useState<Feature[]>([]);
  const [isFetchingFeatures, setIsFetchingFeatures] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const repoFilter = searchParams?.get('repo') || '';

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  /**
   * Fetch all features
   */
  const fetchFeatures = useCallback(async () => {
    setIsFetchingFeatures(true);
    setError(null);
    
    try {
      let url = '/api/v1/repos/features';
      
      console.debug(`Fetching features from: ${url}`);
      
      const response = await apiService.get<{
        features: Feature[];
        total: number;
      }>(url);
      
      console.debug(`Received ${response.features?.length || 0} features`);
      setFeatures(response.features || []);
      
    } catch (err: any) {
      console.error('Error fetching features:', err);
      setError(err.message || 'Failed to load features');
    } finally {
      setIsFetchingFeatures(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && isMounted) {
      fetchFeatures();
    }
  }, [isAuthenticated, isMounted, fetchFeatures]);

  /**
   * Filter features by search query and repo
   */
  useEffect(() => {
    let filtered = features;
    
    // Filter by repo if specified
    if (repoFilter) {
      filtered = filtered.filter(f => f.repository_full_name === repoFilter);
    }
    
    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(f => 
        f.title.toLowerCase().includes(query) ||
        f.branch_name.toLowerCase().includes(query) ||
        f.repository_full_name.toLowerCase().includes(query)
      );
    }
    
    setFilteredFeatures(filtered);
  }, [features, repoFilter, searchQuery]);

  // Prevent hydration mismatch
  if (!isMounted) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading fullScreen />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const handleFeatureClick = (feature: Feature) => {
    router.push(`/editor/${feature.feature_id}`);
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Features
            {repoFilter && (
              <span className="ml-3 text-xl text-gray-600 dark:text-gray-400">
                in {repoFilter}
              </span>
            )}
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Browse and manage features across your repositories.
          </p>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 flex items-center space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search features by name or repository..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
          <button
            onClick={fetchFeatures}
            disabled={isFetchingFeatures}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isFetchingFeatures ? 'Refreshing...' : 'Refresh'}
          </button>
          {repoFilter && (
            <button
              onClick={() => router.push('/features')}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Clear Filter
            </button>
          )}
        </div>

        {/* Features List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          {error && (
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-red-50 dark:bg-red-900/20">
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}
          
          {isFetchingFeatures ? (
            <div className="p-12 text-center">
              <Loading />
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading features...</p>
            </div>
          ) : filteredFeatures.length === 0 ? (
            <div className="p-12 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                No features found
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                {repoFilter 
                  ? `No features found in ${repoFilter}`
                  : searchQuery
                    ? 'Try adjusting your search query'
                    : 'Create your first feature from the dashboard'
                }
              </p>
              <div className="mt-6">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Go to Dashboard
                </button>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredFeatures.map((feature) => (
                <div
                  key={feature.feature_id}
                  className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
                  onClick={() => handleFeatureClick(feature)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        {feature.title || feature.branch_name}
                      </h3>
                      <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        {feature.repository_full_name}
                      </p>
                      <div className="mt-2 flex items-center space-x-4 text-sm">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
                          {feature.branch_name}
                        </span>
                        {feature.base_branch && (
                          <span className="text-gray-500 dark:text-gray-400">
                            from {feature.base_branch}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="ml-4">
                      <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Summary */}
        {!isFetchingFeatures && filteredFeatures.length > 0 && (
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            Showing {filteredFeatures.length} of {features.length} features
          </div>
        )}
      </div>
    </Layout>
  );
}
