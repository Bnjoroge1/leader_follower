import React, { useState, useMemo, useEffect } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import { Header } from "./components/ui/Header";
import { DeviceStatus } from "./components/ui/DeviceStatus";
import { MessageLog } from "./components/ui/MessageLog";
import { SimulationControls } from "./components/ui/SimulationControls";
import { NetworkGraph } from "./components/ui/NetworkGraph";
import { DeviceInfo } from "./types/websocket";
import { Input } from "./components/ui/input";
import { GraphLegend } from "./components/ui/GraphLegend"; // Import the legend component
import { CouncilView } from "./components/ui/CouncilView";

function App() {
  const { connection, device, devices, messages } = useWebSocket();
  const [selectedDevice, setSelectedDevice] = useState<DeviceInfo | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showCouncil, setShowCouncil] = useState(false);
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });

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

  // Handle window resize for fullscreen mode
  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    if (isFullscreen) {
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, [isFullscreen]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'F11' || (event.key === 'f' && event.ctrlKey)) {
        event.preventDefault();
        toggleFullscreen();
      }
      if (event.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };


  return (
    <div className={`flex flex-col ${isFullscreen ? 'h-screen' : 'min-h-screen'}`}>
      {!isFullscreen && <Header connectionStatus={connection} />}

      <main className={`flex-grow ${isFullscreen ? 'h-full p-0' : 'container mx-auto p-4'}`}>
        {isFullscreen ? (
          /* Fullscreen mode - Graph only */
          <div className="relative w-full h-full bg-gray-50">
            <NetworkGraph
              devices={filteredDevices}
              onDeviceSelect={handleNodeClick}
              width={windowSize.width}
              height={windowSize.height}
            />
            {/* Fullscreen toggle button */}
            <button
              onClick={toggleFullscreen}
              className="absolute top-4 left-4 z-20 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg shadow-lg transition-colors"
              title="Exit fullscreen (ESC or F11)"
            >
              Exit Fullscreen
            </button>
            {/* Mini legend in fullscreen */}
            <div className="absolute top-4 right-4 z-20">
              <GraphLegend />
            </div>
          </div>
        ) : (
          /* Normal mode - Split layout */
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Left column - Controls */}
            <div className="xl:col-span-1 space-y-6">
              <DeviceStatus device={device} />
              <SimulationControls />
              <GraphLegend />
              {/* Search Input */}
              <div className="p-4 bg-white rounded-lg shadow-sm">
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

            {/* Right column - Network Graph and Council */}
            <div className="xl:col-span-2 space-y-4">
              {/* Network Graph */}
              <div className="relative">
                <NetworkGraph
                  devices={filteredDevices}
                  onDeviceSelect={handleNodeClick}
                />
                {/* Controls */}
                <div className="absolute top-2 left-2 z-10 flex gap-2">
                  <button
                    onClick={toggleFullscreen}
                    className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-white text-xs rounded shadow-md transition-colors"
                    title="Enter fullscreen (F11 or Ctrl+F)"
                  >
                    Fullscreen
                  </button>
                  <button
                    onClick={() => setShowCouncil(!showCouncil)}
                    className={`px-3 py-1 text-white text-xs rounded shadow-md transition-colors ${showCouncil
                        ? 'bg-blue-600 hover:bg-blue-700'
                        : 'bg-gray-600 hover:bg-gray-700'
                      }`}
                    title="Toggle council view"
                  >
                    {showCouncil ? 'Hide Council' : 'Show Council'}
                  </button>
                </div>
              </div>

              {/* Council View */}
              {showCouncil && (
                <div className="bg-white rounded-lg shadow-sm border">
                  <CouncilView
                    devices={filteredDevices}
                    onDeviceSelect={handleNodeClick}
                    width={800}
                    height={300}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;