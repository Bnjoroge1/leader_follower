import { WS_URL } from '../env';
import { connectionStatus, processWebSocketMessage } from '../stores/websocket';
import { WebSocketMessage } from '../types/websocket';

let socket: WebSocket | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000; // 2 seconds

export function connectWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  connectionStatus.set('connecting');
  
  try {
    socket = new WebSocket(WS_URL);
    
    socket.onopen = () => {
      connectionStatus.set('connected');
      reconnectAttempts = 0;
      console.log('WebSocket connection established');
    };
    
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        processWebSocketMessage(message);
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
      }
    };
    
    socket.onclose = (event) => {
      connectionStatus.set('disconnected');
      console.log('WebSocket connection closed:', event.code, event.reason);
      
      // Attempt to reconnect if the connection was lost (not closed intentionally)
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        setTimeout(() => {
          console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
          connectWebSocket();
        }, RECONNECT_DELAY);
      }
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
  } catch (error) {
    console.error('Failed to connect to WebSocket:', error);
    connectionStatus.set('disconnected');
  }
}

export function disconnectWebSocket() {
  if (socket) {
    socket.close();
    socket = null;
    connectionStatus.set('disconnected');
  }
}

// Automatically reconnect when the window regains focus
export function setupReconnectionListeners() {
  window.addEventListener('focus', () => {
    if (connectionStatus.get() === 'disconnected') {
      connectWebSocket();
    }
  });
}
