export const MISSED_THRESHOLD = 5; // Match the backend value

export interface DeviceInfo {
  id: number;
  task: number | null; // Task can be null or number
  leader: boolean;
  missed: number;
  active: boolean; // Keep optional for now, but we'll primarily use missed
  // Hierarchy fields
  neighborhood_id: number;
  role: 'device' | 'neighborhood_leader' | 'super_leader';
  neighborhood_leader_id: number | null;
  super_leader_id: number | null;
  is_neighborhood_leader: boolean;
  is_super_leader: boolean;
}

export type WebSocketMessage =
  | InitialState
  | MessageLog
  | StatusChange
  | ReceivedMessage
  | DeviceListUpdate;
