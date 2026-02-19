/**
 * WebSocket client service for real-time communication.
 * 
 * Provides:
 * - WebSocket connection management
 * - Auto-reconnect on disconnect
 * - Message queue and replay
 * - Message type routing
 * - Subscription management
 */

'use client';

import { authService } from './auth';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export enum MessageType {
  CONNECTION = 'connection',
  THINKING = 'thinking',
  EXECUTION = 'execution',
  ERROR = 'error',
  COMPLETE = 'complete',
  PROGRESS = 'progress',
  QUESTION = 'question',
  ANSWER = 'answer',
}

export interface WebSocketMessage {
  message_id: string;
  operation_id: string;
  sequence: number;
  type: MessageType;
  content: string;
  data?: any;
  timestamp: string;
  priority: 'low' | 'normal' | 'high' | 'critical';
  is_final: boolean;
  collapsible: boolean;
}

export type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // ms
  private maxReconnectDelay = 30000; // ms
  
  // Message handling
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private globalHandlers: Set<MessageHandler> = new Set();
  
  // Message queue for offline messages
  private messageQueue: WebSocketMessage[] = [];
  
  // Subscriptions
  private subscriptions: Set<string> = new Set();
  
  // Last received sequence per operation
  private lastSequences: Map<string, number> = new Map();
  
  // Connection state
  private connectionId: string | null = null;
  private isConnected = false;

  /**
   * Connect to WebSocket server.
   */
  async connect(): Promise<void> {
    if (this.isConnecting || this.isConnected) {
      console.log('Already connected or connecting');
      return;
    }

    const sessionId = authService.getSessionId();
    if (!sessionId) {
      throw new Error('No active session - cannot connect to WebSocket');
    }

    this.isConnecting = true;

    try {
      const wsUrl = `${WS_BASE_URL}/ws/connect?session_id=${sessionId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);

      console.log('WebSocket connecting...');
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server.
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.connectionId = null;
    this.reconnectAttempts = 0;
  }

  /**
   * Handle WebSocket open event.
   */
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.isConnected = true;
    this.isConnecting = false;
    this.reconnectAttempts = 0;

    // Resubscribe to operations
    this.subscriptions.forEach(operationId => {
      this.sendSubscribe(operationId);
    });
  }

  /**
   * Handle incoming WebSocket message.
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      // Store connection ID from first message
      if (message.type === MessageType.CONNECTION && message.data?.connection_id) {
        this.connectionId = message.data.connection_id;
        console.log('WebSocket connection ID:', this.connectionId);
      }

      // Update last sequence for operation
      this.lastSequences.set(message.operation_id, message.sequence);

      // Route message to handlers
      this.routeMessage(message);

      // Send acknowledgment for important messages
      if (message.priority === 'high' || message.priority === 'critical') {
        this.sendAcknowledgment(message.operation_id, message.sequence);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket error event.
   */
  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
  }

  /**
   * Handle WebSocket close event.
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket closed:', event.code, event.reason);
    
    this.isConnected = false;
    this.isConnecting = false;
    this.ws = null;

    // Attempt reconnect if not intentional close
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt.
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Route message to registered handlers.
   */
  private routeMessage(message: WebSocketMessage): void {
    // Call global handlers
    this.globalHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in global message handler:', error);
      }
    });

    // Call operation-specific handlers
    const operationHandlers = this.messageHandlers.get(message.operation_id);
    if (operationHandlers) {
      operationHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in operation message handler:', error);
        }
      });
    }
  }

  /**
   * Subscribe to operation messages.
   */
  subscribe(operationId: string, handler: MessageHandler): () => void {
    // Add to subscriptions
    this.subscriptions.add(operationId);

    // Send subscribe message if connected
    if (this.isConnected) {
      this.sendSubscribe(operationId);
    }

    // Register handler
    if (!this.messageHandlers.has(operationId)) {
      this.messageHandlers.set(operationId, new Set());
    }
    this.messageHandlers.get(operationId)!.add(handler);

    // Request replay of missed messages
    const lastSequence = this.lastSequences.get(operationId) || 0;
    if (lastSequence > 0) {
      this.requestReplay(operationId, lastSequence);
    }

    // Return unsubscribe function
    return () => {
      this.unsubscribe(operationId, handler);
    };
  }

  /**
   * Unsubscribe from operation messages.
   */
  unsubscribe(operationId: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(operationId);
    if (handlers) {
      handlers.delete(handler);
      
      // Remove operation if no more handlers
      if (handlers.size === 0) {
        this.messageHandlers.delete(operationId);
        this.subscriptions.delete(operationId);
        
        if (this.isConnected) {
          this.sendUnsubscribe(operationId);
        }
      }
    }
  }

  /**
   * Register global message handler.
   */
  onMessage(handler: MessageHandler): () => void {
    this.globalHandlers.add(handler);
    
    return () => {
      this.globalHandlers.delete(handler);
    };
  }

  /**
   * Send subscribe message to server.
   */
  private sendSubscribe(operationId: string): void {
    this.send({
      type: 'subscribe',
      operation_id: operationId,
    });
  }

  /**
   * Send unsubscribe message to server.
   */
  private sendUnsubscribe(operationId: string): void {
    this.send({
      type: 'unsubscribe',
      operation_id: operationId,
    });
  }

  /**
   * Request replay of missed messages.
   */
  private requestReplay(operationId: string, fromSequence: number): void {
    this.send({
      type: 'replay',
      operation_id: operationId,
      from_sequence: fromSequence,
    });
  }

  /**
   * Send acknowledgment for received message.
   */
  private sendAcknowledgment(operationId: string, sequence: number): void {
    this.send({
      type: 'acknowledge',
      operation_id: operationId,
      sequence,
    });
  }

  /**
   * Send message to WebSocket server.
   */
  private send(data: any): void {
    if (this.ws && this.isConnected) {
      try {
        this.ws.send(JSON.stringify(data));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
      }
    } else {
      console.warn('Cannot send message - WebSocket not connected');
    }
  }

  /**
   * Check if connected.
   */
  getIsConnected(): boolean {
    return this.isConnected;
  }

  /**
   * Get connection ID.
   */
  getConnectionId(): string | null {
    return this.connectionId;
  }
}

// Export singleton instance
export const wsService = new WebSocketService();
