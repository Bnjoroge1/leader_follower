type Message = {
  type: 'sent' | 'received';
  action: number;
  payload: number;
  leaderId: number;
  followerId: number;
  timestamp: number;
};

type MessageLogProps = {
  messages: Message[];
};

export function MessageLog({ messages }: MessageLogProps) {
  return (
    <div>
      <h2 className="text-xl font-semibold my-4">Recent Messages</h2>
      <div className="bg-card rounded-lg p-4 shadow max-h-80 overflow-y-auto">
        {messages.length === 0 ? (
          <p>No messages</p>
        ) : (
          <ul className="divide-y">
            {messages.map((msg, index) => (
              <li key={index} className="py-2">
                <p className={msg.type === 'sent' ? 'text-blue-600' : 'text-green-600'}>
                  {msg.type === 'sent' ? 'Sent' : 'Received'} - Action: {msg.action}
                </p>
                <p className="text-sm">
                  Leader: {msg.leaderId}, Follower: {msg.followerId}, Payload: {msg.payload}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
