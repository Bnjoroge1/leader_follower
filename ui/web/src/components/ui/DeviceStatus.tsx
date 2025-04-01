type DeviceStatusProps = {
  device: {
    id: string;
    isLeader: boolean;
    leaderId: string;
  };
};

export function DeviceStatus({ device }: DeviceStatusProps) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Device Status</h2>
      <div className="bg-card rounded-lg p-4 shadow">
        <p>Device ID: <span className="font-mono">{device.id}</span></p>
        <p>Role: {device.isLeader ? 'Leader' : 'Follower'}</p>
        {!device.isLeader && <p>Leader ID: <span className="font-mono">{device.leaderId}</span></p>}
      </div>
    </div>
  );
}
