import React, { useState, useMemo } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import { Header } from "./components/ui/Header";
import { DeviceStatus } from "./components/ui/DeviceStatus";
import { MessageLog } from "./components/ui/MessageLog";
import { SimulationControls } from "./components/ui/SimulationControls";
import { NetworkGraph } from "./components/ui/NetworkGraph";
import { DeviceInfo } from "./types/websocket";
import { Input } from "./components/ui/input";
import { GraphLegend } from "./components/ui/GraphLegend"; // Import the legend component

function App() {
  const { connection, device, devices, messages } = useWebSocket();
  const [selectedDevice, setSelectedDevice] = useState<DeviceInfo | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredDevices = useMemo(() => {
    // ... filtering logic ...
    if (!searchTerm) {
      return devices;
    }
    return devices.filter((d) =>
      String(d.id).toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [devices, searchTerm]);

  const handleNodeClick = (nodeDevice: DeviceInfo | null) => {
    setSelectedDevice(nodeDevice);
  };


  return (
    <div className="flex flex-col min-h-screen">
      <Header connectionStatus={connection} />

      <main className="flex-grow container mx-auto p-4">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left column - Controls */}
          <div className="xl:col-span-1 space-y-6">
            <DeviceStatus device={device} />
            <SimulationControls />
            <GraphLegend /> {/* Add the legend here */}
            {/* Search Input */}
            <div className="p-4 bg-white rounded-lg shadow-sm">
              {/* ... search input label and Input component ... */}
              <label htmlFor="deviceSearch" className="block text-sm font-medium text-gray-700 mb-1">
                Search Device ID
              </label>
              <Input
                id="deviceSearch"
                type="text"
                placeholder="Enter device ID..."
                value={searchTerm}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            {/* Selected Device Info */}
            {selectedDevice && (
              <div className="p-4 bg-white rounded-lg shadow-sm">
                {/* ... selected device details ... */}
                <h3 className="text-lg font-medium mb-2">
                  Selected: Device {selectedDevice.id}
                </h3>
                <p>Status: {selectedDevice.leader ? 'Leader' : 'Follower'}</p>
                <p>Active: {selectedDevice.active ? 'Yes' : 'No'}</p>
                <p>Missed Pings: {selectedDevice.missed}</p>
                {selectedDevice.task && <p>Task: {selectedDevice.task}</p>}
              </div>
            )}
            <MessageLog messages={messages} />
          </div>

          {/* Right column - Network Graph */}
          <div className="xl:col-span-2">
            <NetworkGraph
              devices={filteredDevices}
              onDeviceSelect={handleNodeClick}
            />
          </div>
        </div>
      </main>
    
    </div>
  );
}

export default App;