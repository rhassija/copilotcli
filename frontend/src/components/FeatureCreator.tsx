/**
 * Feature Creator Component
 * 
 * Provides:
 * - Modal dialog for creating new features
 * - Branch name input and validation
 * - Base branch selection
 * - Document initialization toggle
 * - Feature creation with progress feedback
 * 
 * Implements: T097-T099
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { apiService } from '../services/api';
import type { Repository } from './RepoSelector';

export interface Branch {
  name: string;
  commit: {
    sha: string;
    url: string;
  };
  protected: boolean;
  protection_url: string | null;
}

export interface Feature {
  feature_id: string;
  repository_full_name: string;
  branch_name: string;
  base_branch: string;
  title: string;
  status: string;
  spec_path: string | null;
  plan_path: string | null;
  task_path: string | null;
  created_at: string;
  updated_at: string;
  created_by_user_id: number;
}

export interface FeatureCreatorProps {
  repository: Repository;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (feature: Feature) => void;
}

export function FeatureCreator({ repository, isOpen, onClose, onSuccess }: FeatureCreatorProps) {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loadingBranches, setLoadingBranches] = useState(false);
  
  // Form state
  const [featureTitle, setFeatureTitle] = useState('');
  const [branchName, setBranchName] = useState('');
  const [baseBranch, setBaseBranch] = useState('main');
  const [initializeDocuments, setInitializeDocuments] = useState(true);
  
  // UI state
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState('');
  
  /**
   * Fetch branches when modal opens
   */
  useEffect(() => {
    if (isOpen && repository) {
      fetchBranches();
    }
  }, [isOpen, repository]);
  
  /**
   * Auto-generate branch name from title
   */
  useEffect(() => {
    if (featureTitle && !branchName) {
      const generated = 'feature/' + featureTitle
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
      setBranchName(generated);
    }
  }, [featureTitle]);
  
  /**
   * Fetch available branches
   */
  const fetchBranches = async () => {
    if (!repository) return;
    
    setLoadingBranches(true);
    try {
      const [owner, repo] = repository.full_name.split('/');
      const response = await apiService.get<{
        branches: Branch[];
        repository: string;
        total_count: number;
      }>(`/api/v1/repos/${owner}/${repo}/branches`);
      
      setBranches(response.branches);
      
      // Set default base branch
      const defaultBranch = response.branches.find(b => b.name === repository.default_branch);
      if (defaultBranch) {
        setBaseBranch(defaultBranch.name);
      } else if (response.branches.length > 0) {
        setBaseBranch(response.branches[0].name);
      }
    } catch (err: any) {
      console.error('Failed to fetch branches:', err);
      setError('Failed to load branches');
    } finally {
      setLoadingBranches(false);
    }
  };
  
  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!featureTitle.trim()) {
      setError('Feature title is required');
      return;
    }
    
    if (!branchName.trim()) {
      setError('Branch name is required');
      return;
    }
    
    setIsCreating(true);
    setError(null);
    setProgress('Creating branch...');
    
    try {
      const [owner, repo] = repository.full_name.split('/');
      
      const response = await apiService.post<{
        branch: Branch;
        feature_id: string;
        message: string;
        documents_initialized: boolean;
        spec_path: string | null;
        plan_path: string | null;
        task_path: string | null;
      }>(`/api/v1/repos/${owner}/${repo}/branches`, {
        branch_name: branchName,
        from_branch: baseBranch,
        feature_title: featureTitle,
        initialize_documents: initializeDocuments,
      });
      
      if (initializeDocuments) {
        setProgress('Initializing documents via Copilot CLI...');
        // Wait a bit for visual feedback
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      setProgress('Feature created successfully!');
      
      // Create feature object for callback
      const feature: Feature = {
        feature_id: response.feature_id,
        repository_full_name: repository.full_name,
        branch_name: branchName,
        base_branch: baseBranch,
        title: featureTitle,
        status: 'active',
        spec_path: response.spec_path,
        plan_path: response.plan_path,
        task_path: response.task_path,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        created_by_user_id: 0, // Will be set by backend
      };
      
      // Call success callback
      onSuccess(feature);
      
      // Reset form and close
      setTimeout(() => {
        handleClose();
      }, 500);
      
    } catch (err: any) {
      console.error('Failed to create feature:', err);
      setError(err.response?.data?.error?.message || err.message || 'Failed to create feature');
    } finally {
      setIsCreating(false);
    }
  };
  
  /**
   * Handle modal close
   */
  const handleClose = () => {
    if (!isCreating) {
      setFeatureTitle('');
      setBranchName('');
      setBaseBranch('main');
      setInitializeDocuments(true);
      setError(null);
      setProgress('');
      onClose();
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
            ✨ Create New Feature
          </h2>
          <button
            onClick={handleClose}
            disabled={isCreating}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-50"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Repository Info */}
          <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-md">
            <p className="text-sm text-gray-600 dark:text-gray-400">Repository:</p>
            <p className="font-medium text-gray-900 dark:text-white">{repository.full_name}</p>
          </div>
          
          {/* Feature Title */}
          <div>
            <label htmlFor="featureTitle" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Feature Title <span className="text-red-500">*</span>
            </label>
            <input
              id="featureTitle"
              type="text"
              value={featureTitle}
              onChange={(e) => setFeatureTitle(e.target.value)}
              placeholder="e.g., Add real-time collaboration support"
              disabled={isCreating}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              required
            />
          </div>
          
          {/* Branch Name */}
          <div>
            <label htmlFor="branchName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Branch Name <span className="text-red-500">*</span>
            </label>
            <input
              id="branchName"
              type="text"
              value={branchName}
              onChange={(e) => setBranchName(e.target.value)}
              placeholder="e.g., feature/010-realtime-collab"
              disabled={isCreating}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              required
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Auto-generated from title. Use lowercase with hyphens.
            </p>
          </div>
          
          {/* Base Branch */}
          <div>
            <label htmlFor="baseBranch" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Base Branch
            </label>
            {loadingBranches ? (
              <div className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-900">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Loading branches...</span>
              </div>
            ) : (
              <select
                id="baseBranch"
                value={baseBranch}
                onChange={(e) => setBaseBranch(e.target.value)}
                disabled={isCreating}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {branches.map((branch) => (
                  <option key={branch.name} value={branch.name}>
                    {branch.name} {branch.name === repository.default_branch && '(default)'}
                  </option>
                ))}
              </select>
            )}
          </div>
          
          {/* Initialize Documents */}
          <div className="flex items-start gap-3">
            <input
              id="initDocs"
              type="checkbox"
              checked={initializeDocuments}
              onChange={(e) => setInitializeDocuments(e.target.checked)}
              disabled={isCreating}
              className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50"
            />
            <label htmlFor="initDocs" className="text-sm text-gray-700 dark:text-gray-300">
              <span className="font-medium">Initialize documents (spec/plan/tasks)</span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Automatically create initial specification, plan, and task documents using Copilot CLI
              </p>
            </label>
          </div>
          
          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}
          
          {/* Progress Message */}
          {isCreating && progress && (
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                <p className="text-sm text-blue-700 dark:text-blue-400">{progress}</p>
              </div>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex gap-3 justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              disabled={isCreating}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isCreating || !featureTitle.trim() || !branchName.trim()}
              className="px-6 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isCreating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Creating...
                </>
              ) : (
                <>
                  Create Feature →
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
