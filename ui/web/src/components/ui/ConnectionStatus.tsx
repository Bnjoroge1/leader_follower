type ConnectionStatusProps = {
  status: 'connected' | 'disconnected' | 'connecting';
};

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  return (
    <div className="flex items-center gap-2">
      <div 
        className={`h-3 w-3 rounded-full ${
          status === 'connected' 
            ? 'bg-green-500' 
            : status === 'connecting' 
              ? 'bg-yellow-500' 
              : 'bg-red-500'
        }`}
      />
      <span>
        {status === 'connected' 
          ? 'Connected' 
          : status === 'connecting' 
            ? 'Connecting...' 
            : 'Disconnected'
        }
      </span>
    </div>
  );
}
