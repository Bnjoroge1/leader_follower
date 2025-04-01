export interface InitialState {
  type: 'initial_state';
  device_id: string;
  leader_id: string;
  is_leader: boolean;
  device_list: DeviceInfo[];
}

export interface MessageLog {
  type: 'message_log';
  timestamp: number;
  data: {
    type: 'send';
    action: number;
    payload: number;
    leader_id: number;
    follower_id: number;
  };
}

export interface StatusChange {
  type: 'status_change';
  timestamp: number;
  data: {
    is_leader: boolean;
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
  };
}

export interface DeviceListUpdate {
  type: 'device_list';
  timestamp: number;
  data: DeviceInfo[];
}

export interface DeviceInfo {
  id: string;
  task?: string;
  leader: boolean;
  missed: number;
}

export type WebSocketMessage = 
  | InitialState 
  | MessageLog 
  | StatusChange 
  | ReceivedMessage 
  | DeviceListUpdate;
