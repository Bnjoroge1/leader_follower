import { atom } from 'nanostores';
import { persistentAtom } from '@nanostores/persistent';
import { DeviceInfo, WebSocketMessage } from '../types/websocket';

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
export const recentMessages = atom<{
  type: 'sent' | 'received';
  action: number;
  payload: number;
  leaderId: number;
  followerId: number;
  timestamp: number;
}[]>([]);

// Add a new message to the recent messages store
export function addMessage(
  type: 'sent' | 'received',
  action: number,
  payload: number,
  leaderId: number,
  followerId: number
) {
  const messages = recentMessages.get();
  const newMessage = {
    type,
    action,
    payload,
    leaderId,
    followerId,
    timestamp: Date.now()
  };
  
  // Keep only the last 50 messages
  if (messages.length >= 50) {
    recentMessages.set([...messages.slice(1), newMessage]);
  } else {
    recentMessages.set([...messages, newMessage]);
  }
}

// Process messages from the WebSocket
export function processWebSocketMessage(message: WebSocketMessage) {
  switch (message.type) {
    case 'initial_state':
      currentDevice.set({
        id: message.device_id,
        isLeader: message.is_leader,
        leaderId: message.leader_id
      });
      deviceList.set(message.device_list);
      break;
      
    case 'message_log':
      if (message.data.type === 'send') {
        addMessage(
          'sent',
          message.data.action,
          message.data.payload,
          message.data.leader_id,
          message.data.follower_id
        );
      }
      break;
      
    case 'status_change':
      currentDevice.set({
        ...currentDevice.get(),
        isLeader: message.data.is_leader
      });
      break;
      
    case 'received_message':
      addMessage(
        'received',
        message.data.action,
        message.data.payload,
        message.data.leader_id,
        message.data.follower_id
      );
      break;
      
    case 'device_list':
      deviceList.set(message.data);
      break;
  }
}
