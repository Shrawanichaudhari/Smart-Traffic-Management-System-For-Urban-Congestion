// WebSocket service for real-time traffic data updates

import type { WebSocketMessage } from '../types/simulation';
import type { CityWebSocketMessage } from '../types/city';

type EventCallback = (data: any) => void;
type ConnectionStatusCallback = (connected: boolean) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000; // 5 seconds
  private pingInterval: NodeJS.Timeout | null = null;
  private eventListeners: { [key: string]: EventCallback[] } = {};
  private connectionStatusListeners: ConnectionStatusCallback[] = [];
  private isConnected = false;

  private readonly wsUrl: string;

  constructor() {
    // Vite: prefer VITE_TRAFFIC_WS_URL, fallback to legacy env, then to localhost.
    const viteUrl = (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_TRAFFIC_WS_URL) as
      | string
      | undefined;
    const legacyHost = (typeof process !== 'undefined' && (process as any).env?.REACT_APP_WS_HOST) as string | undefined;

    if (viteUrl) {
      this.wsUrl = viteUrl;
      return;
    }

    // Legacy fallback: build URL from host.
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = legacyHost || window.location.host.replace(':3000', ':8001');

    // Default to the new city endpoint.
    this.wsUrl = `${protocol}//${host}/ws/city`;
  }

  // Connect to WebSocket
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket is already connected');
      return;
    }

    try {
      console.log(`Connecting to WebSocket: ${this.wsUrl}`);
      this.ws = new WebSocket(this.wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.handleConnectionError();
    }
  }

  // Disconnect from WebSocket
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    
    this.isConnected = false;
    this.notifyConnectionStatus(false);
  }

  // Set up WebSocket event handlers
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected successfully');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.notifyConnectionStatus(true);
      this.startPingInterval();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage | CityWebSocketMessage | any;
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket closed. Code: ${event.code}, Reason: ${event.reason}`);
      this.isConnected = false;
      this.notifyConnectionStatus(false);
      
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
      
      // Attempt to reconnect if connection was not closed intentionally
      if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.attemptReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.handleConnectionError();
    };
  }

  // Handle incoming WebSocket messages
  private handleMessage(message: any): void {
    if (!message || typeof message.type !== 'string') {
      return;
    }

    console.log('Received WebSocket message:', message.type);

    switch (message.type) {
      // Legacy simulation messages
      case 'simulation_update':
        if (message.data) {
          this.emit('simulationUpdate', message.data);
        }
        break;

      // City real-time messages
      case 'city_update':
        this.emit('cityUpdate', message);
        break;
      case 'incident_update':
        this.emit('incidentUpdate', message);
        break;
      case 'ambulance_route_update':
        this.emit('ambulanceRouteUpdate', message);
        break;

      case 'connection_status':
        this.emit('connectionStatus', { status: message.message, timestamp: message.timestamp });
        break;

      case 'pong':
        this.emit('pong', message);
        break;

      case 'error':
        console.error('WebSocket server error:', message.message);
        this.emit('error', { error: message.message, timestamp: message.timestamp });
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }

  // Attempt to reconnect
  private attemptReconnect(): void {
    this.reconnectAttempts++;
    console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        this.connect();
      } else {
        console.error('Max reconnection attempts reached. Please refresh the page.');
        this.emit('maxReconnectAttemptsReached', {});
      }
    }, this.reconnectInterval);
  }

  // Handle connection errors
  private handleConnectionError(): void {
    this.isConnected = false;
    this.notifyConnectionStatus(false);
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.attemptReconnect();
    }
  }

  // Start ping interval to keep connection alive
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // Ping every 30 seconds
  }

  // Add event listener
  on(event: string, callback: EventCallback): void {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(callback);
  }

  // Remove event listener
  off(event: string, callback: EventCallback): void {
    if (this.eventListeners[event]) {
      this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
    }
  }

  // Add connection status listener
  onConnectionStatus(callback: ConnectionStatusCallback): void {
    this.connectionStatusListeners.push(callback);
  }

  // Remove connection status listener
  offConnectionStatus(callback: ConnectionStatusCallback): void {
    this.connectionStatusListeners = this.connectionStatusListeners.filter(cb => cb !== callback);
  }

  // Emit event to listeners
  private emit(event: string, data: any): void {
    if (this.eventListeners[event]) {
      this.eventListeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  // Notify connection status listeners
  private notifyConnectionStatus(connected: boolean): void {
    this.connectionStatusListeners.forEach(callback => {
      try {
        callback(connected);
      } catch (error) {
        console.error('Error in connection status listener:', error);
      }
    });
  }

  // Get current connection status
  getConnectionStatus(): boolean {
    return this.isConnected;
  }

  // Send message to server (if needed)
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
export default websocketService;