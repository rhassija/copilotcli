/**
 * Dashboard page - Main application interface after authentication.
 * 
 * Displays repositories, features, and workflow interfaces.
 * 
 * Implements: T101
 */

'use client';

import { useAuth } from '../../hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import Loading from '../../components/Loading';
import { RepoSelector, type Repository } from '../../components/RepoSelector';
import { FeatureCreator, type Feature } from '../../components/FeatureCreator';
import { FeatureList } from '../../components/FeatureList';

export default function DashboardPage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);
  
  // Repository and feature state
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [isFeatureCreatorOpen, setIsFeatureCreatorOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  // Prevent hydration mismatch by waiting for client-side mount
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
    return null; // Will redirect in useEffect
  }
  
  /**
   * Handle repository selection
   */
  const handleRepoSelect = (repo: Repository) => {
    setSelectedRepo(repo);
  };
  
  /**
   * Handle feature creation success
   */
  const handleFeatureCreated = (feature: Feature) => {
    setIsFeatureCreatorOpen(false);
    // Trigger refresh of feature list
    setRefreshKey(prev => prev + 1);
  };
  
  /**
   * Handle refresh button
   */
  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome back{user?.login ? `, ${user.login}` : ''}!
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Select a repository and create features to get started with your workflow.
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Repository Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <RepoSelector
              onSelect={handleRepoSelect}
              selectedRepo={selectedRepo}
            />
          </div>

          {/* Right Column: Features */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            {selectedRepo ? (
              <div className="space-y-4">
                {/* Header with Create Button */}
                <div className="flex items-center justify-between pb-4 border-b border-gray-200 dark:border-gray-700">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                      📦 {selectedRepo.name}
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {selectedRepo.description || 'No description'}
                    </p>
                  </div>
                  <button
                    onClick={() => setIsFeatureCreatorOpen(true)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors flex items-center gap-2"
                  >
                    <span>+</span>
                    Create Feature
                  </button>
                </div>
                
                {/* Feature List */}
                <FeatureList
                  key={refreshKey}
                  repository={selectedRepo}
                  onRefresh={handleRefresh}
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="text-6xl mb-4">📦</div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No Repository Selected
                </h3>
                <p className="text-gray-500 dark:text-gray-400 max-w-sm">
                  Select a repository from the left to view and manage its features
                </p>
              </div>
            )}
          </div>
        </div>
        
        {/* Info Cards */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 dark:text-blue-400 mb-2">
              💡 Quick Tip
            </h3>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Create a feature to initialize spec, plan, and task documents automatically
            </p>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <h3 className="font-medium text-green-900 dark:text-green-400 mb-2">
              🚀 Getting Started
            </h3>
            <p className="text-sm text-green-700 dark:text-green-300">
              Features are tracked branches with associated documentation for organized development
            </p>
          </div>
          
          <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
            <h3 className="font-medium text-purple-900 dark:text-purple-400 mb-2">
              📚 Documentation
            </h3>
            <p className="text-sm text-purple-700 dark:text-purple-300">
              Each feature includes spec, plan, and tasks documents synced with GitHub
            </p>
          </div>
        </div>
      </div>
      
      {/* Feature Creator Modal */}
      {selectedRepo && (
        <FeatureCreator
          repository={selectedRepo}
          isOpen={isFeatureCreatorOpen}
          onClose={() => setIsFeatureCreatorOpen(false)}
          onSuccess={handleFeatureCreated}
        />
      )}
    </Layout>
  );
}
