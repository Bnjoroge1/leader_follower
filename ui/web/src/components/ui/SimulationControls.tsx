
import React, { useState } from 'react';
import { useStore } from '@nanostores/react';
import { deviceList } from '../../stores/websocket'; // Adjust import path
import { Button } from './button'; // Assuming you have a Button component
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select'; // Assuming shadcn/ui select

// Define the base URL for your simulation API
const API_BASE_URL = 'http://localhost:8080/simulate'; 

async function sendSimulationCommand(command: string, deviceId: string | number) {
  if (!deviceId) {
    alert('Please select a device ID.');
    return;
  }
  const url = `${API_BASE_URL}/${command}/${deviceId}`;
  console.log(`Sending command: POST ${url}`);
  try {
    const response = await fetch(url, { method: 'POST' });
    const text = await response.text();
    if (!response.ok) {
      throw new Error(`API Error (${response.status}): ${text}`);
    }
    console.log(`Command ${command} for ${deviceId} successful: ${text}`);
    alert(`Command ${command} for ${deviceId} sent: ${text}`);
  } catch (error) {
    console.error(`Failed to send command ${command} for ${deviceId}:`, error);
    alert(`Failed to send command ${command} for ${deviceId}: ${error instanceof Error ? error.message : String(error)}`);
  }
}

export function SimulationControls() {
  const devices = useStore(deviceList);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');

  const handleDeviceChange = (value: string) => {
    setSelectedDeviceId(value);
  };

  return (
    <div className="mt-6 p-4 border rounded-lg shadow bg-card">
      <h2 className="text-xl font-semibold mb-4">Simulation Controls</h2>
      <div className="flex flex-wrap gap-4 items-center">
        <Select value={selectedDeviceId} onValueChange={handleDeviceChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select Device ID" />
          </SelectTrigger>
          <SelectContent>
            {devices.map(d => (
              <SelectItem key={d.id} value={String(d.id)}>
                Device {d.id} {d.leader ? '(L)' : ''}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button variant="destructive" size="sm" onClick={() => sendSimulationCommand('stop', selectedDeviceId)} disabled={!selectedDeviceId}>
          Stop Process
        </Button>
         {/* <Button variant="secondary" size="sm" onClick={() => sendSimulationCommand('start', selectedDeviceId)} disabled={!selectedDeviceId}>
          Start Process
        </Button> */}
        <Button variant="outline" size="sm" onClick={() => sendSimulationCommand('deactivate', selectedDeviceId)} disabled={!selectedDeviceId}>
          Deactivate
        </Button>
        <Button variant="outline" size="sm" onClick={() => sendSimulationCommand('activate', selectedDeviceId)} disabled={!selectedDeviceId}>
          Activate
        </Button>
      </div>
       <p className="text-xs text-muted-foreground mt-2">
         Note: 'Stop Process' attempts to terminate the device's simulation process. 'Deactivate'/'Activate' toggle the internal active flag.
       </p>
    </div>
  );
}