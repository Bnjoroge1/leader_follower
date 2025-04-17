import { atom } from 'nanostores';
import { persistentAtom } from '@nanostores/persistent';
// Ensure DeviceInfo and WebSocketMessage types are correctly defined/imported
import { DeviceInfo, WebSocketMessage, MessageLogData } from '../types/websocket';

// Store the connection status
export const connectionStatus = atom<'connected' | 'disconnected' | 'connecting'>('disconnected');

// Store the current device's information
export const currentDevice = persistentAtom<{
  id: string;
  isLeader: boolean;
  leaderId: string;
}>('current-device', { id: '', isLeader: false, leaderId: '' }, {
  encode: JSON.stringify,
  decode: JSON.parse
});

// Store the list of devices
export const deviceList = atom<DeviceInfo[]>([]);

// Store for recent messages (limited to last 50)
// Let's update the store type to match the structure we decided on for MessageLog.tsx
export type LogStoreEntry = {
  data: MessageLogData; // Store the nested data object
  timestamp: number;
};
export const recentMessages = atom<LogStoreEntry[]>([]);

// Update addMessage to accept the MessageLogData object
export function addMessage(logData: MessageLogData) {
  const messages = recentMessages.get();
  const newEntry: LogStoreEntry = {
    data: logData,
    timestamp: Date.now() // Use client-side timestamp for simplicity, or use server's if needed
  };

  // Keep only the last 50 messages
  recentMessages.set([
      ...messages.slice(-49), // Keep last 50 entries
      newEntry
  ]);
  console.log('Added message to store:', newEntry); // Add log here
  console.log('Current recentMessages:', recentMessages.get()); // Log the whole store
}

// Process messages from the WebSocket
export function processWebSocketMessage(message: WebSocketMessage) {
  console.log('Processing WebSocket message type:', message.type);

  switch (message.type) {
    case 'initial_state':
      console.log('Processing initial_state with device list:', message.device_list);
      currentDevice.set({
        id: message.device_id,
        isLeader: message.is_leader,
        leaderId: String(message.leader_id) // Ensure leaderId is a string
      });
      // Ensure device list data matches DeviceInfo[] type
      if (Array.isArray(message.device_list)) {
         deviceList.set(message.device_list);
      } else {
         console.error("Received initial_state with invalid device_list format:", message.device_list);
         deviceList.set([]); // Set to empty array on error
      }
      console.log('Updated device list store:', deviceList.get());
      break;

    case 'message_log':
      console.log('Processing message_log:', message.data); // Log the received data
      // Handle both 'receive' and 'would_send' types from the nested data
      if (message.data && (message.data.type === 'receive' || message.data.type === 'would_send' || message.data.type === 'log_event')) {
         // Pass the entire data object to addMessage
         addMessage(message.data);
      } else {
         console.warn('Received message_log with unexpected data type:', message.data?.type);
      }
      break;

    case 'status_change':
      console.log('Processing status_change:', message.data); // Log the received data
      currentDevice.set({
        ...currentDevice.get(),
        // Assuming status_change data has is_leader and leader_id
        isLeader: message.data.is_leader,
        leaderId: String(message.data.leader_id) // Ensure leaderId is a string
      });
      console.log('Updated current device store:', currentDevice.get());
      break;

    case 'device_list':
      console.log('Processing device_list update:', message.data);
      // Ensure device list data matches DeviceInfo[] type
      if (Array.isArray(message.data)) {
         deviceList.set(message.data);
      } else {
         console.error("Received device_list update with invalid format:", message.data);
         // Optionally keep the old list or set to empty
         // deviceList.set([]);
      }
      console.log('Updated device list store:', deviceList.get());
      break;
    

    default:
       console.warn('Received unhandled WebSocket message type:', (message as any)?.type);
  }
}
