import { MessageLogData } from '../../types/websocket'; // Import the correct type
import { getActionName } from '../../types/actions';
import { recentMessages, LogStoreEntry } from '../../stores/websocket';
import { useStore } from '@nanostores/react';


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
    case 13: return `${direction}: Activate Device ${follower_id}`;
    case 14: return `${direction}: Deactivate Device ${follower_id}`;
    default: return `${direction}: Unknown Action ${action} (L:${leader_id}, F:${follower_id}, P:${payload})`;
  }
}

// Helper function to get color class based on action
function getMessageColor(logEntry: LogStoreEntry): string {
  const data = logEntry.data;
  if (data.type === 'log_event') {
      // Use level for API events
      return getLogLevelColor(data.level);
  } else {
      // Use action for protocol messages (receive/would_send)
      switch (data.action) {
          case 1: return 'text-blue-600 dark:text-blue-400'; // Attendance
          case 2: return 'text-blue-500 dark:text-blue-300'; // Attendance Response
          case 3: return 'text-purple-600 dark:text-purple-400'; // D_List
          case 4: return 'text-cyan-600 dark:text-cyan-400'; // Check-In
          case 5: return 'text-red-600 dark:text-red-400'; // Delete
          case 6: return 'text-cyan-500 dark:text-cyan-300'; // Check-In Response
          case 7: return 'text-green-600 dark:text-green-400'; // New Follower
          case 8: return 'text-yellow-600 dark:text-yellow-400'; // New Leader
          case 9: return 'text-orange-600 dark:text-orange-400'; // Rejoin Request
          case 10: return 'text-orange-500 dark:text-orange-300'; // Rejoin Response
          case 11: return 'text-orange-500 dark:text-orange-300'; // Rejoin Announce (same as response?)
          case 12: return 'text-indigo-600 dark:text-indigo-400'; // Candidacy
          case 13: return 'text-lime-600 dark:text-lime-400'; // Activate
          case 14: return 'text-pink-600 dark:text-pink-400'; // Deactivate
          default: return 'text-gray-500 dark:text-gray-400'; // Unknown action
      }
  }
}
// Helper function to get color based on log level
function getLogLevelColor(level?: string): string {
  switch (level?.toUpperCase()) {
    case 'WARN':
      return 'text-yellow-600 dark:text-yellow-400'; // Warning color
    case 'ERROR': // Add error handling if needed
      return 'text-red-600 dark:text-red-400';
    case 'INFO':
    default:
      return 'text-blue-600 dark:text-blue-400'; // Default/Info color
  }
}
// Helper function to format the message content
function formatMessageContent(logEntry: LogStoreEntry): string {
  const data = logEntry.data;
  switch (data.type) {
    case 'receive':
      // Use the helper function to get the name
      return `Received: Action=${getActionName(data.action)}, L=${data.leader_id}, F=${data.follower_id}, P=${data.payload}`;
    case 'would_send':
      // Use the helper function to get the name
      return `Simulated Send: Action=${getActionName(data.action)}, L=${data.leader_id}, F=${data.follower_id}, P=${data.payload}`;
    case 'log_event': // Handle API log events
      return `API Event: ${data.message}`; // Use the message field directly
    default:
      // Ensure exhaustive check or handle unknown types
      //const exhaustiveCheck: never = data.type; 
      return `Unknown log type: ${JSON.stringify(data)}`; // Fallback
  }
}


export function MessageLog({ messages }: MessageLogProps) {
  const displayedMessages = useStore(recentMessages); // Use the store directly

  return (
    <div>
      <h2 className="text-xl font-semibold my-4">Message Log</h2>
      <div className="bg-card rounded-lg p-4 shadow h-64 overflow-y-auto text-sm font-mono">
        {displayedMessages.length === 0 ? (
          <p className="text-muted-foreground">No messages yet</p>
        ) : (
          <ul className="space-y-1">
            {/* Reverse is handled by the store logic now, iterate normally */}
            {displayedMessages.map((entry: { timestamp: any; data: any; }, index: any) => (
              <li key={`${entry.timestamp}-${index}`} className={`${getMessageColor(entry)}`}> {/* Apply color based on action or level */}
                <span className="text-muted-foreground mr-2">
                  [{new Date(entry.timestamp).toLocaleTimeString()}]
                  {/* Show source device ID or 'API server' */}
                  [{entry.data.device_id ?? 'N/A'}]: 
                </span>
                {formatMessageContent(entry)}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}