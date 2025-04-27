import { DeviceInfo, MISSED_THRESHOLD } from '../../types/websocket';

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
            {devices.map(device => {
              // Determine text color: Red if inactive, else Green if leader, else Blue
              let textColor = 'text-blue-500'; // Default follower blue
              if (!device.active) { // Prioritize active status
                  textColor = 'text-red-500'; // Red for inactive
              } else if (device.leader) {
                  textColor = 'text-green-500'; // Green for leader
              }
              // No need for the missed check here if active status is reliable

              return (
                <li
                  key={device.id}
                  className={`py-2 ${textColor}`} // Apply dynamic text color class
                >
                  <p>ID: <span className="font-mono">{device.id}</span>
                    {/* Optionally show (Inactive) based on active flag */}
                    {!device.active && <span className="ml-2">(Inactive)</span>}
                  </p>
                  <p>Role: {device.leader ? 'Leader' : 'Follower'}</p>
                  {device.task && <p>Task: {device.task}</p>}
                  <p>Missed: {device.missed}</p>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
