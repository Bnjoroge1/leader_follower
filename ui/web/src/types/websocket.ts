export interface InitialState {
  type: 'initial_state';
  device_id: string;
  leader_id: string;
  is_leader: boolean;
  device_list: DeviceInfo[];
}
export interface MessageLogData {
  type: 'receive' | 'would_send'; // Type from UI device perspective
  action: number;
  leader_id: number;
  follower_id: number;
  payload: number;
  raw?: number | string; // Raw message integer or string
  device_id: number; // ID of the UI device logging this
}

export interface MessageLog {
  type: 'message_log';
  timestamp: number;
  data: MessageLogData;
}

export interface StatusChange {
  type: 'status_change';
  timestamp: number;
  data: {
    is_leader: boolean;
    leader_id: number;
    
  };
}
export interface CandidateUpdate {
  type: 'candidate_update';
  timestamp: number;
  data: {
    is_leader: boolean;
    leader_id: number;
  };
}

export interface ReceivedMessage {
  type: 'received_message';
  timestamp: number;
  data: {
    action: number;
    leader_id: number;
    follower_id: number;
    payload: number;
    raw: string;
    device_id: string;
  };
}

export interface DeviceListUpdate {
  type: 'device_list';
  timestamp: number;
  data: DeviceInfo[];
}

export interface DeviceInfo {
  id: number;
  task?: string | number | null;
  leader: boolean;
  missed: number;
}

export type WebSocketMessage = 
  | InitialState 
  | MessageLog 
  | StatusChange 
  | ReceivedMessage 
  | DeviceListUpdate;
