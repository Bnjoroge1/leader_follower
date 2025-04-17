
export enum Action {
  CANDIDACY = 0,
  ATTENDANCE = 1,
  ATT_RESPONSE = 2,
  D_LIST = 3,
  CHECK_IN = 4,
  DELETE = 5,
  NEW_LEADER = 6,
  TASK_START = 7,
  CHECK_IN_RESPONSE = 8,
  INFORMATION = 9,
  // Note: REJOIN actions reuse numbers 10, 11, 12
  REJOIN_REQUEST = 10, 
  REJOIN_RESPONSE = 11,
  REJOIN_ANNOUNCE = 12,
  // Original OFF/ON/NEW_FOLLOWER might conflict or be unused?
  // OFF = 10, 
  // ON = 11,
  // NEW_FOLLOWER = 12, 
  ACTIVATE = 13,
  DEACTIVATE = 14,
}

// Helper to get name, handling potential conflicts/unknowns
export function getActionName(actionValue: number | undefined): string {
  if (actionValue === undefined) return 'UNKNOWN';
  // Handle potential overlaps if needed, otherwise just use the enum name
  const actionName = Action[actionValue];
  return actionName ?? `UNKNOWN (${actionValue})`;
}