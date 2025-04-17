import { DeviceInfo } from '../../types/websocket';

type DeviceListProps = {
  devices: DeviceInfo[];
};

export function DeviceList({ devices }: DeviceListProps) {
  return (
    <div>
      <h2 className="text-xl font-semibold my-4">Connected Devices</h2>
      <div className="bg-card rounded-lg p-4 shadow">
        {devices.length === 0 ? (
          <p>No devices connected</p>
        ) : (
          <ul className="divide-y">
            {devices.map(device => (
              <li 
                key={device.id} 
                className={`py-2 ${device.active === false ? 'text-red-500' : (device.leader ? 'text-green-500' : 'text-blue-500')}`}
              >
                <p>ID: <span className="font-mono">{device.id}</span> 
                  {device.active === false && <span className="ml-2">(Stopped)</span>}
                </p>
                <p>Role: {device.leader ? 'Leader' : 'Follower'}</p>
                {device.task && <p>Task: {device.task}</p>}
                <p>Missed: {device.missed}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
