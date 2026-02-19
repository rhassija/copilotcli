/**
 * Repositories page - Browse and select repositories.
 * 
 * Displays searchable repository list with filters.
 */

'use client';

import { useAuth } from '../../hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import Loading from '../../components/Loading';
import { RepoSelector, type Repository } from '../../components/RepoSelector';

export default function RepositoriesPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

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
  
  const handleRepoSelect = (repo: Repository) => {
    setSelectedRepo(repo);
    // Navigate to dashboard with selected repo or features page
    router.push(`/features?repo=${repo.full_name}`);
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Repositories
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Browse and select a repository to view features or create new ones.
          </p>
        </div>

        {/* Repository Selector */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <RepoSelector
            onSelect={handleRepoSelect}
            selectedRepo={selectedRepo}
          />
        </div>

        {/* Selected Repository Info */}
        {selectedRepo && (
          <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Selected Repository
            </h2>
            <div className="flex items-start space-x-4">
              <img 
                src={selectedRepo.owner.avatar_url} 
                alt={selectedRepo.owner.login}
                className="w-16 h-16 rounded-md"
              />
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {selectedRepo.full_name}
                </h3>
                {selectedRepo.description && (
                  <p className="mt-1 text-gray-600 dark:text-gray-400">
                    {selectedRepo.description}
                  </p>
                )}
                <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                  {selectedRepo.language && (
                    <span className="flex items-center">
                      <span className="w-3 h-3 rounded-full bg-blue-500 mr-1"></span>
                      {selectedRepo.language}
                    </span>
                  )}
                  <span>⭐ {selectedRepo.stargazers_count}</span>
                  <span>🍴 {selectedRepo.forks_count}</span>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => router.push(`/features?repo=${selectedRepo.full_name}`)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    View Features
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
