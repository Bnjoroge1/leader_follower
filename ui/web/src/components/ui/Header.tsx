import { ConnectionStatus } from './ConnectionStatus';

type HeaderProps = {
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
};

export function Header({ connectionStatus }: HeaderProps) {
  return (
    <header className="p-4 border-b">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold">Leader-Follower System</h1>
        <ConnectionStatus status={connectionStatus} />
      </div>
    </header>
  );
}
