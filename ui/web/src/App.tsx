import { useEffect } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import TrackBox from "./components/track-box";
import { Header } from "./components/ui/Header";
import { DeviceStatus } from "./components/ui/DeviceStatus";
import { DeviceList } from "./components/ui/DeviceList";
import { MessageLog } from "./components/ui/MessageLog";

function App() {
  const { connection, device, devices, messages } = useWebSocket();
  
  useEffect(() => {
    // Log when the connection status changes
    console.log('WebSocket connection status:', connection);
  }, [connection]);

  return (
    <div className="flex flex-col min-h-screen">
      <Header connectionStatus={connection} />
      
      <main className="flex-grow container mx-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <DeviceStatus device={device} />
            <DeviceList devices={devices} />
          </div>
          
          <div>
            <h2 className="text-xl font-semibold mb-4">Track Box</h2>
            <TrackBox onCellClick={(num) => { console.log(`Cell ${num} clicked!`); }} />
            <MessageLog messages={messages} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;