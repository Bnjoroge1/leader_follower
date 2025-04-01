import { useEffect } from 'react';
import { useStore } from '@nanostores/react';
import { connectWebSocket, disconnectWebSocket, setupReconnectionListeners } from '../lib/websocket';
import { connectionStatus, currentDevice, deviceList, recentMessages } from '../stores/websocket';

export function useWebSocket() {
  const connection = useStore(connectionStatus);
  const device = useStore(currentDevice);
  const devices = useStore(deviceList);
  const messages = useStore(recentMessages);

  useEffect(() => {
    // Connect to the WebSocket when the component mounts
    connectWebSocket();
    setupReconnectionListeners();

    // Disconnect when the component unmounts
    return () => {
      disconnectWebSocket();
    };
  }, []);

  return {
    connection,
    device,
    devices,
    messages,
    connect: connectWebSocket,
    disconnect: disconnectWebSocket,
  };
}
