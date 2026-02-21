/**
 * Document Editor Page - Multi-tab editor for spec, plan, and task documents
 * 
 * Displays and edits spec.md, plan.md, and task.md for a feature
 * with automatic saving, unsaved changes detection, and markdown support.
 * 
 * Implements: T117-T127 (Document editor UI components and saving)
 */

'use client';

import { useAuth } from '../../../hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Layout from '../../../components/Layout';
import Loading from '../../../components/Loading';
import DocumentEditor from '../../../components/DocumentEditors/DocumentEditor';
import { apiService } from '../../../services/api';

export interface DocumentContent {
  content: string;
  sha: string;
  last_modified: string;
  path: string;
  repository: string;
  branch: string;
}

export interface AllDocuments {
  feature_id: string;
  spec?: DocumentContent;
  plan?: DocumentContent;
  task?: DocumentContent;
}

type TabType = 'spec' | 'plan' | 'task';

const TABS: { id: TabType; label: string; icon: string }[] = [
  { id: 'spec', label: 'Specification', icon: '📄' },
  { id: 'plan', label: 'Plan', icon: '📋' },
  { id: 'task', label: 'Tasks', icon: '✅' },
];

export default function EditorPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const featureId = params.featureId as string;

  // State
  const [activeTab, setActiveTab] = useState<TabType>('spec');
  const [documents, setDocuments] = useState<AllDocuments | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unsavedChanges, setUnsavedChanges] = useState<Partial<Record<TabType, boolean>>>({
    spec: false,
    plan: false,
    task: false,
  });
  const [isMounted, setIsMounted] = useState(false);

  // Initialize
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Check authentication
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  // Load documents
  useEffect(() => {
    if (!isMounted || !featureId || !isAuthenticated) return;

    const loadDocuments = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await apiService.get<AllDocuments>(
          `/api/v1/features/${featureId}/documents`
        );

        setDocuments(response);
      } catch (err: any) {
        console.error('Failed to load documents:', err);
        setError(
          err.response?.data?.detail ||
          err.message ||
          'Failed to load documents'
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadDocuments();
  }, [featureId, isAuthenticated, isMounted]);

  if (!isMounted) {
    return null;
  }

  if (authLoading || isLoading) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <Loading fullScreen />
        </div>
      </Layout>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (error) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto py-8">
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <h2 className="text-lg font-semibold text-red-900 dark:text-red-400 mb-2">
              Error Loading Documents
            </h2>
            <p className="text-red-700 dark:text-red-300 mb-4">{error}</p>
            <button
              onClick={() => router.back()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md"
            >
              Go Back
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const currentDoc = documents?.[activeTab];
  const hasUnsavedChanges = Object.values(unsavedChanges).some(v => v);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.back()}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
              >
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  📝 Workflow Editor
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Feature ID: {featureId}
                </p>
              </div>
            </div>

            {/* Unsaved Indicator */}
            {hasUnsavedChanges && (
              <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
                <span className="text-lg">⚠️</span>
                <span className="text-sm font-medium text-yellow-900 dark:text-yellow-400">
                  Unsaved Changes
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 font-medium text-base transition-colors border-b-2 ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300'
              } ${unsavedChanges[tab.id] ? 'after:content-["*"] after:ml-1' : ''}`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
              {unsavedChanges[tab.id] && (
                <span className="ml-1 text-red-600 dark:text-red-400">*</span>
              )}
            </button>
          ))}
        </div>

        {/* Editor Content */}
        {currentDoc ? (
          <DocumentEditor
            key={`${featureId}-${activeTab}`}
            featureId={featureId}
            docType={activeTab}
            document={currentDoc}
            onSave={() => {
              setUnsavedChanges((prev) => ({
                ...prev,
                [activeTab]: false,
              }));
            }}
            onMarkUnsaved={() => {
              setUnsavedChanges((prev) => ({
                ...prev,
                [activeTab]: true,
              }));
            }}
          />
        ) : (
          <CreateDocumentPrompt
            featureId={featureId}
            docType={activeTab}
            onSuccess={() => {
              // Reload documents
              const loadDocuments = async () => {
                const response = await apiService.get<AllDocuments>(
                  `/api/v1/features/${featureId}/documents`
                );
                setDocuments(response);
              };
              loadDocuments();
            }}
          />
        )}
      </div>

      {/* Unsaved Changes Warning */}
      {hasUnsavedChanges && (
        <div className="fixed bottom-4 right-4 p-4 bg-white dark:bg-gray-800 border border-yellow-300 dark:border-yellow-600 rounded-lg shadow-lg">
          <p className="text-sm text-gray-900 dark:text-white mb-3">
            💾 You have unsaved changes in this document
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">
            Auto-save is disabled. Click Save in the editor to save your changes.
          </p>
        </div>
      )}
    </Layout>
  );
}

interface CreateDocumentPromptProps {
  featureId: string;
  docType: TabType;
  onSuccess: () => void;
}

function CreateDocumentPrompt({
  featureId,
  docType,
  onSuccess,
}: CreateDocumentPromptProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    setIsCreating(true);
    setError(null);

    try {
      await apiService.post(
        `/api/v1/features/${featureId}/document/${docType}`,
        {}
      );

      onSuccess();
    } catch (err: any) {
      console.error('Failed to create document:', err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to create document'
      );
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="max-w-md p-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-center shadow-sm">
        <div className="text-6xl mb-4">📝</div>
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {docType.charAt(0).toUpperCase() + docType.slice(1)} Not Found
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          This {docType} document doesn't exist yet. Create one from a template
          to get started.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}

        <button
          onClick={handleCreate}
          disabled={isCreating}
          className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-md transition-colors"
        >
          {isCreating ? (
            <>
              <span className="inline-block animate-spin mr-2">⟳</span>
              Creating...
            </>
          ) : (
            `Create ${docType.charAt(0).toUpperCase() + docType.slice(1)} from Template`
          )}
        </button>
      </div>
    </div>
  );
}
