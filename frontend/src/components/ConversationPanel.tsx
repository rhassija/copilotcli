/**
 * ConversationPanel Component
 * 
 * Displays real-time WebSocket messages from Copilot CLI operations.
 * Shows thinking, execution, error, and complete message types.
 * Supports collapsible thinking sections and auto-scroll.
 * 
 * Implements: T148-T152 (WebSocket Live UI component)
 * 
 * Features:
 * - Real-time message streaming via WebSocket
 * - Message type rendering (thinking/execution/error/complete)
 * - Collapsible thinking sections
 * - Auto-scroll to latest message
 * - Message timestamps and sender labels
 * - Connection status indicator
 * - Clear/close functionality
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { wsService } from '../services/websocket';

export interface Message {
  id: string;
  type: 'thinking' | 'execution' | 'error' | 'complete' | 'info';
  content: string;
  timestamp: number;
  sender: string;
}

export interface ConversationPanelProps {
  operationId: string;
  isOpen: boolean;
  onClose?: () => void;
  title?: string;
  showThinking?: boolean;
  onToggleThinking?: (show: boolean) => void;
}

export default function ConversationPanel({
  operationId,
  isOpen,
  onClose,
  title = 'Operation Progress',
  showThinking = true,
  onToggleThinking,
}: ConversationPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());
  const [localShowThinking, setLocalShowThinking] = useState(showThinking);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 0);
  }, []);

  // Connect to WebSocket for this operation
  useEffect(() => {
    if (!isOpen || !operationId) return;

    const handleMessage = (message: any) => {
      console.debug('ConversationPanel received message:', message);
      
      const newMessage: Message = {
        id: `${Date.now()}-${Math.random()}`,
        type: message.type || 'info',
        content: message.content || JSON.stringify(message),
        timestamp: Date.now(),
        sender: message.sender || 'Copilot CLI',
      };

      setMessages(prev => [...prev, newMessage]);
      scrollToBottom();
    };

    const handleConnect = () => {
      console.debug('ConversationPanel WebSocket connected');
      setIsConnected(true);
    };

    const handleDisconnect = () => {
      console.debug('ConversationPanel WebSocket disconnected');
      setIsConnected(false);
    };

    const handleError = (error: any) => {
      console.error('ConversationPanel WebSocket error:', error);
      const messageText =
        error?.message ||
        error?.reason ||
        (typeof error === 'string' ? error : 'WebSocket connection error');
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: 'error',
        content: `Connection error: ${messageText}`,
        timestamp: Date.now(),
        sender: 'System',
      };
      setMessages(prev => [...prev, errorMessage]);
    };

    // Ensure WebSocket connection and subscribe to operation
    wsService.connect().catch(handleError);
    wsService.subscribe(operationId, handleMessage);
    wsService.on('connect', handleConnect);
    wsService.on('disconnect', handleDisconnect);
    wsService.on('error', handleError);

    // Check if already connected
    const connected = wsService.getIsConnected();
    setIsConnected(connected);

    return () => {
      wsService.unsubscribe(operationId, handleMessage);
      wsService.off('connect', handleConnect);
      wsService.off('disconnect', handleDisconnect);
      wsService.off('error', handleError);
    };
  }, [isOpen, operationId, scrollToBottom]);

  // Handle thinking toggle
  const handleToggleThinking = () => {
    const newValue = !localShowThinking;
    setLocalShowThinking(newValue);
    onToggleThinking?.(newValue);
  };

  // Toggle section collapse
  const toggleSection = (sectionId: string) => {
    setCollapsedSections(prev => {
      const next = new Set(prev);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return next;
    });
  };

  // Filter messages based on thinking visibility
  const filteredMessages = messages.filter(msg => {
    if (msg.type === 'thinking' && !localShowThinking) {
      return false;
    }
    return true;
  });

  // Group consecutive thinking messages
  const groupedMessages = filteredMessages.reduce((acc: any[], msg) => {
    if (msg.type === 'thinking') {
      const lastGroup = acc[acc.length - 1];
      if (lastGroup?.type === 'thinking' && lastGroup.isGroup) {
        lastGroup.messages.push(msg);
      } else {
        acc.push({
          type: 'thinking',
          isGroup: true,
          messages: [msg],
          id: `thinking-group-${msg.timestamp}`,
        });
      }
    } else {
      acc.push(msg);
    }
    return acc;
  }, []);

  // Get message type color
  const getMessageColor = (type: string) => {
    switch (type) {
      case 'thinking':
        return 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800';
      case 'execution':
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'complete':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      default:
        return 'bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800';
    }
  };

  // Get message icon
  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'thinking':
        return '🧠';
      case 'execution':
        return '⚙️';
      case 'error':
        return '❌';
      case 'complete':
        return '✅';
      default:
        return 'ℹ️';
    }
  };

  // Format timestamp
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className="fixed bottom-0 right-0 w-96 h-80 bg-white dark:bg-gray-800 border-l border-t border-gray-200 dark:border-gray-700 shadow-2xl flex flex-col z-50"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleToggleThinking}
            title={localShowThinking ? 'Hide thinking' : 'Show thinking'}
            className={`p-1 rounded text-xs transition-colors ${
              localShowThinking
                ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}
          >
            🧠
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {groupedMessages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              <p>Waiting for messages...</p>
              <p className="text-xs mt-1">Operation {operationId}</p>
            </div>
          </div>
        ) : (
          groupedMessages.map((item: any) => {
            if (item.isGroup && item.type === 'thinking') {
              const isCollapsed = collapsedSections.has(item.id);
              const thinkingContent = item.messages.map((m: Message) => m.content).join('\n');

              return (
                <div
                  key={item.id}
                  className={`border rounded-lg p-3 ${getMessageColor('thinking')}`}
                >
                  <button
                    onClick={() => toggleSection(item.id)}
                    className="flex items-start gap-2 w-full text-left hover:opacity-75 transition-opacity"
                  >
                    <span className="text-lg mt-0.5">{getMessageIcon('thinking')}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                          Thinking
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          ({item.messages.length} steps)
                        </span>
                        <span className="ml-auto text-xs text-gray-500 dark:text-gray-400">
                          {isCollapsed ? '▶' : '▼'}
                        </span>
                      </div>
                      {!isCollapsed && (
                        <pre className="mt-2 text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words font-mono bg-white/50 dark:bg-gray-800/50 p-2 rounded max-h-32 overflow-y-auto">
                          {thinkingContent}
                        </pre>
                      )}
                    </div>
                  </button>
                </div>
              );
            }

            const msg = item as Message;
            return (
              <div key={msg.id} className={`border rounded-lg p-3 ${getMessageColor(msg.type)}`}>
                <div className="flex items-start gap-2">
                  <span className="text-lg mt-0.5">{getMessageIcon(msg.type)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300 capitalize">
                        {msg.type}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatTime(msg.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
                      {msg.content}
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-xs text-gray-500 dark:text-gray-400">
        {messages.length} message{messages.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}
