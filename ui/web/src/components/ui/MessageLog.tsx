import { MessageLogData } from '../../types/websocket'; // Import the correct type

// Define the structure stored in the recentMessages array
type LogStoreEntry = {
  data: MessageLogData;
  timestamp: number;
};

type MessageLogProps = {
  messages: LogStoreEntry[]; // Expect the structure from the store
};

// Helper function to get descriptive text for an action
// Update function signature to accept MessageLogData directly
function getActionText(logData: MessageLogData): string {
  const { action, leader_id, follower_id, payload, type } = logData; // Destructure from logData
  const direction = type === 'would_send' ? 'UI Would Send' : 'UI Received';

  switch (action) {
    case 1: return `${direction}: Leader ${leader_id} Attendance`;
    case 2: return `${direction}: Follower ${follower_id} Attendance Response`;
    case 3: return `${direction}: Leader ${leader_id} D_List for ${follower_id} (Task: ${payload})`;
    case 4: return `${direction}: Leader ${leader_id} Check-In for ${follower_id}`;
    case 5: return `${direction}: Leader ${leader_id} Delete for ${follower_id}`;
    case 6: return `${direction}: Follower ${follower_id} Check-In Response`;
    case 7: return `${direction}: Device ${follower_id} New Follower Announcement`;
    case 8: return `${direction}: Device ${leader_id} New Leader Announcement`;
    case 9: return `${direction}: Follower ${follower_id} Rejoin Request to ${leader_id}`;
    case 10: return `${direction}: Leader ${leader_id} Rejoin Response to ${follower_id}`;
    case 11: return `${direction}: Leader ${leader_id} Rejoin Announce for ${follower_id}`;
    case 12: return `${direction}: Device ${leader_id} Candidacy Broadcast`;
    // Add cases for ACTIVATE/DEACTIVATE if used
    // case 13: return `${direction}: Activate Device ${follower_id}`;
    // case 14: return `${direction}: Deactivate Device ${follower_id}`;
    default: return `${direction}: Unknown Action ${action} (L:${leader_id}, F:${follower_id}, P:${payload})`;
  }
}

// Helper function to get color class based on action
function getActionColor(action: number): string {
  switch (action) {
    case 1: return 'text-blue-600'; // Attendance
    case 2: return 'text-blue-400'; // Attendance Response
    case 3: return 'text-purple-600'; // D_List
    case 4: return 'text-cyan-600'; // Check-In
    case 5: return 'text-red-600'; // Delete
    case 6: return 'text-cyan-400'; // Check-In Response
    case 7: return 'text-green-600'; // New Follower
    case 8: return 'text-yellow-600'; // New Leader
    case 9: return 'text-orange-600'; // Rejoin Request
    case 10: return 'text-orange-400'; // Rejoin Response
    case 11: return 'text-orange-500'; // Rejoin Announce
    case 12: return 'text-indigo-600'; // Candidacy
    default: return 'text-gray-500'; // Unknown
  }
}

export function MessageLog({ messages }: MessageLogProps) {
  return (
    <div>
      <h2 className="text-xl font-semibold my-4">Recent Messages</h2>
      <div className="bg-card rounded-lg p-4 shadow max-h-80 overflow-y-auto">
        {messages.length === 0 ? (
          <p>No messages</p>
        ) : (
          <ul className="divide-y">
            {/* Reverse the messages array to show newest first */}
            {messages.slice().reverse().map((msg, index) => (
              // Use msg.timestamp or index for key if msg.data.raw is not unique/available
              <li key={`${msg.timestamp}-${index}`} className="py-2">
                {/* Apply color based on action inside msg.data */}
                <p className={`font-medium ${getActionColor(msg.data.action)}`}>
                  {/* Pass the nested data object to getActionText */}
                  {getActionText(msg.data)}
                </p>
                {/* Optionally display raw message if needed */}
                {/* <p className="text-xs text-gray-400">Raw: {msg.data.raw}</p> */}
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
