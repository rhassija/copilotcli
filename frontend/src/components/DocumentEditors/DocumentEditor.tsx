/**
 * Document Editor Component
 * 
 * Provides markdown editing for spec, plan, and task documents with:
 * - Live markdown preview
 * - Save functionality with optimistic locking
 * - Unsaved changes detection
 * - Auto-save within debounced intervals
 * - Real-time WebSocket updates via ConversationPanel
 * 
 * Implements: T117-T120, T148-T152 (Tab layout, document editing, live updates)
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import { apiService } from '@/services/api';
import MarkdownPreview from './MarkdownPreview';
import ConversationPanel from '../ConversationPanel';

export interface DocumentContent {
  content: string;
  sha: string;
  last_modified: string;
  path: string;
  repository: string;
  branch: string;
}

interface DocumentEditorProps {
  featureId: string;
  docType: 'spec' | 'plan' | 'task';
  document: DocumentContent;
  onSave: () => void;
  onMarkUnsaved: () => void;
}

export default function DocumentEditor({
  featureId,
  docType,
  document,
  onSave,
  onMarkUnsaved,
}: DocumentEditorProps) {
  const [content, setContent] = useState(document.content);
  const [currentSha, setCurrentSha] = useState(document.sha);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState(document.last_modified);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [operationId, setOperationId] = useState<string | null>(null);
  const [showConversation, setShowConversation] = useState(false);
  const [showThinking, setShowThinking] = useState(true);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  /**
   * Handle content change
   */
  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    setHasChanges(true);
    setError(null);
    onMarkUnsaved();

    // Debounce auto-save attempt (but don't actually auto-save, just mark as unsaved)
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
  };

  /**
   * Save document to GitHub
   */
  const handleSave = useCallback(async () => {
    if (!hasChanges) return;

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null); // Clear success message on save

    try {
      const response = await apiService.put(
        `/api/v1/features/${featureId}/${docType}`,
        {
          content,
          sha: currentSha,
          message: `Update ${docType} document`,
        }
      );

      setCurrentSha(response.sha);
      setLastSavedAt(new Date().toISOString());
      setHasChanges(false);
      setError(null);
      setSuccessMessage('Document saved successfully to GitHub! 🎉');
      
      // Auto-dismiss success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
      
      onSave();
    } catch (err: any) {
      console.error('Failed to save document:', err);

      // Handle optimistic locking conflict
      if (err.response?.status === 409) {
        setError(
          'Document has been modified elsewhere. Please refresh to see the latest version.'
        );
      } else {
        setError(
          err.response?.data?.detail ||
          err.message ||
          'Failed to save document'
        );
      }
    } finally {
      setIsSaving(false);
    }
  }, [featureId, docType, content, currentSha, hasChanges, onSave]);

  /**
   * Generate document with Copilot CLI
   */
  const handleGenerate = useCallback(async (requirementDescription: string, enableCopilot: boolean, copilotModel?: string) => {
    const newOperationId = `${docType}-${featureId}-${Date.now()}`;
    setOperationId(newOperationId);
    setShowConversation(true);
    setIsGenerating(true);
    setError(null);
    setShowGenerateModal(false);

    try {
      // Use longer timeout for Copilot CLI operations (10 minutes)
      // Spec generation can take 7-10 minutes depending on complexity and Copilot processing
      const response = await apiService.post<{
        content: string;
        used_copilot: boolean;
        model_used: string | null;
        message: string;
      }>(
        `/api/v1/features/${featureId}/generate-${docType}`,
        {
          requirement_description: requirementDescription,
          enable_copilot: enableCopilot,
          copilot_model: copilotModel || null,
          include_context: true,
          operation_id: newOperationId,
        },
        {
          timeout: 600000, // 10 minutes (600 seconds) for Copilot CLI generation
        }
      );

      // Replace content with generated content
      setContent(response.content);
      setHasChanges(true);
      onMarkUnsaved();
      
      // Show success message with call-to-action
      setError(null);
      setSuccessMessage(`${docType.charAt(0).toUpperCase() + docType.slice(1)} generated successfully! Click "Save" to persist to GitHub.`);
    } catch (err: any) {
      console.error('Failed to generate document:', err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to generate document with Copilot CLI'
      );
    } finally {
      setIsGenerating(false);
    }
  }, [featureId, docType, onMarkUnsaved]);

  /**
   * Format date for display
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Conversation Panel */}
      {operationId && (
        <ConversationPanel
          operationId={operationId}
          isOpen={showConversation}
          onClose={() => setShowConversation(false)}
          title={`${docType.charAt(0).toUpperCase() + docType.slice(1)} Generation`}
          showThinking={showThinking}
          onToggleThinking={setShowThinking}
        />
      )}
      {/* Document Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {document.repository} / {document.branch} / {document.path}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            Last saved: {formatDate(lastSavedAt)}
          </p>
        </div>

        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={() => setShowGenerateModal(true)}
            disabled={isGenerating || isSaving}
            className="px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white text-sm font-medium rounded-md transition-colors flex items-center gap-2"
            title="Generate with Copilot CLI"
          >
            {isGenerating ? (
              <>
                <span className="inline-block animate-spin">⟳</span>
                Generating...
              </>
            ) : (
              <>
                🤖 Generate
              </>
            )}
          </button>
          
          <button
            onClick={() => setShowPreview(!showPreview)}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              showPreview
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
            }`}
          >
            {showPreview ? '👁️ Preview' : '✏️ Edit'}
          </button>

          <button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium rounded-md transition-colors flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <span className="inline-block animate-spin">⟳</span>
                Saving...
              </>
            ) : (
              <>
                💾 Save
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="px-6 py-4 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
          <p className="text-sm text-red-700 dark:text-red-400 flex items-start gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </p>
        </div>
      )}
      
      {/* Success Message */}
      {successMessage && (
        <div className="px-6 py-4 bg-green-50 dark:bg-green-900/20 border-b border-green-200 dark:border-green-800">
          <p className="text-sm text-green-700 dark:text-green-400 flex items-start gap-2">
            <span>✅</span>
            <span>{successMessage}</span>
          </p>
        </div>
      )}

      {/* Editor/Preview Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Edit View */}
        {!showPreview && (
          <textarea
            value={content}
            onChange={(e) => handleContentChange(e.target.value)}
            className="flex-1 p-6 font-mono text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white border-0 focus:outline-none resize-none"
            placeholder="Enter document content in Markdown format..."
            spellCheck="false"
          />
        )}

        {/* Preview View */}
        {showPreview && (
          <div className="flex-1 overflow-auto">
            <MarkdownPreview content={content} />
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-xs text-gray-600 dark:text-gray-400">
        <div>
          {hasChanges ? (
            <span className="text-yellow-600 dark:text-yellow-400">
              ⚠️ Unsaved changes
            </span>
          ) : (
            <span className="text-green-600 dark:text-green-400">
              ✓ All changes saved
            </span>
          )}
        </div>

        <div className="flex items-center gap-4">
          <span>{content.length} characters</span>
          <span>{content.split('\n').length} lines</span>
        </div>
      </div>

      {/* Generate Modal */}
      {showGenerateModal && (
        <GenerateModal
          docType={docType}
          onGenerate={handleGenerate}
          onClose={() => setShowGenerateModal(false)}
        />
      )}
    </div>
  );
}

// Simple Generate Modal Component
interface GenerateModalProps {
  docType: string;
  onGenerate: (requirement: string, enableCopilot: boolean, model?: string) => void;
  onClose: () => void;
}

function GenerateModal({ docType, onGenerate, onClose }: GenerateModalProps) {
  const [requirement, setRequirement] = useState('');
  const [enableCopilot, setEnableCopilot] = useState(true);
  const [model, setModel] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (requirement.trim().length >= 10) {
      onGenerate(requirement, enableCopilot, model || undefined);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            🤖 Generate {docType.toUpperCase()} with Copilot CLI
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Feature Requirement <span className="text-red-500">*</span>
            </label>
            <textarea
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              placeholder="Describe your feature requirement in natural language..."
              rows={6}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 resize-y"
              required
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Minimum 10 characters. The more detail you provide, the better the generated document.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="enableCopilot"
              checked={enableCopilot}
              onChange={(e) => setEnableCopilot(e.target.checked)}
              className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            />
            <label htmlFor="enableCopilot" className="text-sm text-gray-700 dark:text-gray-300">
              Use Copilot CLI enrichment
            </label>
          </div>

          {enableCopilot && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Model (optional)
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Default</option>
                <option value="gpt-4">GPT-4</option>
                <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
              </select>
            </div>
          )}

          <div className="flex gap-3 justify-end pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={requirement.trim().length < 10}
              className="px-6 py-2 text-white bg-purple-600 hover:bg-purple-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🚀 Generate
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
