/**
 * Markdown Preview Component
 * 
 * Renders markdown content with syntax highlighting and formatting.
 * Uses a simple markdown rendering approach (can be enhanced with 
 * react-markdown or unified later).
 * 
 * Implements: Part of T117-T120 (Document preview)
 */

'use client';

import { useMemo } from 'react';

interface MarkdownPreviewProps {
  content: string;
}

/**
 * Simple markdown to HTML converter
 * For production, use react-markdown or similar library
 */
function renderMarkdown(markdown: string): string {
  let html = markdown || '';

  // Escape HTML special characters (except for markdown syntax we're processing)
  html = html.replace(/&/g, '&amp;');
  html = html.replace(/</g, '&lt;');
  html = html.replace(/>/g, '&gt;');

  // Code blocks
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (_match, _lang, code) => {
    return `<pre class="bg-gray-100 dark:bg-gray-900 p-3 rounded-md overflow-x-auto my-2"><code class="text-gray-800 dark:text-gray-200 text-sm">${code.trim()}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-sm font-mono">$1</code>');

  // Headers
  html = html.replace(/^### (.*?)$/gm, '<h3 class="text-lg font-bold text-gray-900 dark:text-white mt-4 mb-2">$1</h3>');
  html = html.replace(/^## (.*?)$/gm, '<h2 class="text-xl font-bold text-gray-900 dark:text-white mt-6 mb-3">$1</h2>');
  html = html.replace(/^# (.*?)$/gm, '<h1 class="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">$1</h1>');

  // Bold and italic
  html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/__\(.*?\)__/g, '<strong>$1</strong>');
  html = html.replace(/_(.*?)_/g, '<em>$1</em>');

  // Links
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="text-blue-600 dark:text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>');

  // List items (bullet points)
  html = html.replace(/^\* (.*?)$/gm, '<li class="ml-4 text-gray-800 dark:text-gray-200">$1</li>');
  html = html.replace(/^- (.*?)$/gm, '<li class="ml-4 text-gray-800 dark:text-gray-200">$1</li>');

  // Checkboxes
  html = html.replace(/- \[x\] (.*?)$/gmi, '<li class="ml-4 flex items-center gap-2 text-gray-800 dark:text-gray-200"><input type="checkbox" checked disabled class="rounded"> $1</li>');
  html = html.replace(/- \[ \] (.*?)$/gm, '<li class="ml-4 flex items-center gap-2 text-gray-800 dark:text-gray-200"><input type="checkbox" disabled class="rounded"> $1</li>');

  // Blockquotes
  html = html.replace(/^> (.*?)$/gm, '<blockquote class="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic text-gray-600 dark:text-gray-400 my-2">$1</blockquote>');

  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr class="border-t border-gray-300 dark:border-gray-600 my-4">');
  html = html.replace(/^\*\*\*$/gm, '<hr class="border-t border-gray-300 dark:border-gray-600 my-4">');

  // Line breaks
  html = html.replace(/\n\n/g, '</p><p class="my-2">');
  html = `<p class="my-2">${html}</p>`;

  return html;
}

export default function MarkdownPreview({ content }: MarkdownPreviewProps) {
  const htmlContent = useMemo(() => renderMarkdown(content || ''), [content]);

  return (
    <div className="p-6 overflow-auto h-full bg-white dark:bg-gray-800">
      <div
        dangerouslySetInnerHTML={{ __html: htmlContent }}
        className="prose dark:prose-invert max-w-none prose-sm sm:prose-base text-gray-800 dark:text-gray-200 space-y-4"
      />
    </div>
  );
}
