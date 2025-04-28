export const MISSED_THRESHOLD = 5; // Match the backend value

export interface DeviceInfo {
  id: number;
  task: number | null; // Task can be null or number
  leader: boolean;
  missed: number;
  active: boolean; // Keep optional for now, but we'll primarily use missed
  // Add other fields if they exist in the data sent from ui_device.py format_device_list
  // e.g., leader_id: number | null;
}

export type WebSocketMessage = 
  | InitialState 
  | MessageLog 
  | StatusChange 
  | ReceivedMessage 
  | DeviceListUpdate;
