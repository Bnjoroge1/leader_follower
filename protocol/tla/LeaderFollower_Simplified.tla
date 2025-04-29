---- MODULE LeaderFollower_Simplified ----
EXTENDS Naturals, FiniteSets, Sequences, TLC

\* This model focuses on the core leader election logic and state transitions.
\* It simplifies or omits:
\* - Realistic time and timeouts (Timeout actions and related variables removed)
\* - Network unreliability (message loss, reordering, duplication)
\* - Device failures/recovery (DOWN state exists but transitions into/out of it aren't modeled)
\* - Detailed device list management (D_LIST)
\* - Message payloads and task assignment

CONSTANTS
    MaxDevices, \* Maximum number of devices in the system
    NULL        \* Represents no known leader

VARIABLES
    status,         \* Function: device ID -> { "DOWN", "CANDIDATE", "FOLLOWER", "LEADER" }
    leader_known,   \* Function: device ID -> known leader ID (or NULL)
    messages        \* Sequence of messages in transit, each a record: [type |-> Str, from |-> Nat, to |-> Nat]

vars == <<status, leader_known, messages>>

\* Assume devices are numbered 1 to MaxDevices
DevicesSet == 1..MaxDevices

\* Status values
DOWN      == "DOWN"
CANDIDATE == "CANDIDATE"
FOLLOWER  == "FOLLOWER"
LEADER    == "LEADER"

\* Message types
CLAIM_LEADER == "CLAIM_LEADER" \* Sent by candidate wanting to be leader
ACK_LEADER   == "ACK_LEADER"   \* Sent by follower acknowledging a leader
CHECK_IN     == "CHECK_IN"     \* Sent by leader to followers (simplified)
CHECK_IN_RESP== "CHECK_IN_RESP" \* Sent by follower to leader (simplified)

\* Message record type for TypeOK invariant
MessageRecord == [type: {CLAIM_LEADER, ACK_LEADER, CHECK_IN, CHECK_IN_RESP}, from: DevicesSet, to: DevicesSet \union {NULL}]

\* Initial state
Init ==
    \* Assume all devices start as candidates initially.
    \* To model devices starting DOWN, modify this initialization.
    /\ status = [d \in DevicesSet |-> CANDIDATE]
    /\ leader_known = [d \in DevicesSet |-> NULL]
    /\ messages = <<>>

\* Action: A candidate decides to claim leadership.
\* Simplification: Any candidate can attempt to claim leadership.
\* The HandleClaimLeader action enforces the lowest ID rule implicitly.
CandidateClaimsLeadership(d) ==
    /\ status[d] = CANDIDATE
    \* Device decides it wants to be leader (perhaps because leader_known[d] = NULL)
    /\ status' = [status EXCEPT ![d] = LEADER] \* Tentatively becomes leader
    /\ leader_known' = [leader_known EXCEPT ![d] = d] \* Knows itself as leader
    \* Broadcast claim (represented by message with NULL recipient, or multiple messages could be modeled)
    /\ messages' = Append(messages, [type |-> CLAIM_LEADER, from |-> d, to |-> NULL])
    /\ UNCHANGED << >> \* No other variables changed by this action itself

\* Action: A device receives a leadership claim message.
HandleClaimLeader(recipient) ==
    /\ messages /= <<>>
    /\ LET msg == Head(messages)
       claimant == msg.from
    IN /\ msg.type = CLAIM_LEADER
       /\ status[recipient] /= DOWN \* Only non-DOWN devices process claims
       /\ IF leader_known[recipient] = NULL \/ claimant <= leader_known[recipient] THEN
            \* Accept if no known leader or claimant has lower/equal ID
            /\ status' = [status EXCEPT ![recipient] = FOLLOWER]
            /\ leader_known' = [leader_known EXCEPT ![recipient] = claimant]
            \* Send acknowledgment back to the claimant
            /\ messages' = Tail(messages) \o <<[type |-> ACK_LEADER, from |-> recipient, to |-> claimant]>>
       ELSE \* Ignore claim (current leader is lower ID)
            /\ messages' = Tail(messages)
            /\ UNCHANGED <<status, leader_known>>

\* Action: Leader processes an acknowledgment from a follower.
\* (This confirms the follower accepted the leader)
LeaderProcessesAck(l) ==
    /\ status[l] = LEADER
    /\ messages /= <<>>
    /\ LET msg == Head(messages)
       responder == msg.from
    IN /\ msg.type = ACK_LEADER
       /\ msg.to = l
       \* Leader now knows 'responder' is a follower.
       \* (In a more complex model, leader might update a follower list here)
       /\ messages' = Tail(messages)
       /\ UNCHANGED <<status, leader_known>>

\* --- Simplified Check-in Mechanism (Optional, focuses on state) ---
\* This is highly simplified as timeouts are not modeled.
\* It mainly shows state transitions related to check-ins.

\* Action: Leader sends check-in to a known follower.
LeaderSendsCheckIn(l) ==
    /\ status[l] = LEADER
    /\ \E f \in DevicesSet:
        /\ status[f] = FOLLOWER
        /\ leader_known[f] = l \* Only ping followers who acknowledge this leader
        \* Non-deterministically choose one follower to ping
        /\ messages' = Append(messages, [type |-> CHECK_IN, from |-> l, to |-> f])
        /\ UNCHANGED <<status, leader_known>>

\* Action: Follower responds to check-in from its known leader.
FollowerRespondsCheckIn(f) ==
    /\ status[f] = FOLLOWER
    /\ messages /= <<>>
    /\ LET msg == Head(messages)
    IN /\ msg.type = CHECK_IN
       /\ msg.to = f
       /\ msg.from = leader_known[f] \* Respond only to known leader
       /\ messages' = Tail(messages) \o <<[type |-> CHECK_IN_RESP, from |-> f, to |-> msg.from]>>
       /\ UNCHANGED <<status, leader_known>>

\* Action: Leader processes check-in response.
LeaderProcessesResponse(l) ==
    /\ status[l] = LEADER
    /\ messages /= <<>>
    /\ LET msg == Head(messages)
    IN /\ msg.type = CHECK_IN_RESP
       /\ msg.to = l
       \* Leader received response, knows follower is active.
       /\ messages' = Tail(messages)
       /\ UNCHANGED <<status, leader_known>>

\* --- End Simplified Check-in ---


\* Next state relation: Defines all possible steps the system can take.
Next ==
    \/ \E d \in DevicesSet : CandidateClaimsLeadership(d)
    \/ \E r \in DevicesSet : HandleClaimLeader(r)
    \/ \E l \in DevicesSet : LeaderProcessesAck(l)
    \* Include check-in actions if desired:
    \/ \E l \in DevicesSet : LeaderSendsCheckIn(l)
    \/ \E f \in DevicesSet : FollowerRespondsCheckIn(f)
    \/ \E l \in DevicesSet : LeaderProcessesResponse(l)


\* == Invariants (Safety Properties) ==

\* At most one device can be in the LEADER state at any time.
AtMostOneLeader ==
    Cardinality({d \in DevicesSet : status[d] = LEADER}) <= 1

\* If a device is LEADER, it must have the lowest ID among all non-DOWN devices.
\* Note: This depends on the assumption that lower IDs eventually win claims.
LeaderIsLowestActive ==
    \A l \in DevicesSet:
        (status[l] = LEADER) => (\A d \in DevicesSet \ {l}: status[d] /= DOWN => d > l)

\* Type invariant: Ensures variables stay within their expected types/domains.
TypeOK ==
    /\ status \in [DevicesSet -> {DOWN, CANDIDATE, FOLLOWER, LEADER}]
    /\ leader_known \in [DevicesSet -> DevicesSet \union {NULL}]
    /\ \A msg \in messages: DOMAIN msg = {"type", "from", "to"} /\ msg.type \in {CLAIM_LEADER, ACK_LEADER, CHECK_IN, CHECK_IN_RESP} /\ msg.from \in DevicesSet /\ msg.to \in DevicesSet \union {NULL}
    \* Alternative, slightly weaker check for messages:
    \* /\ messages \in Seq(MessageRecord)


\* == Liveness Property ==

\* Eventually, if there are active (non-DOWN) devices, a leader should be selected.
\* Requires fairness assumption (WF_vars) so actions don't get ignored forever.
EventuallyHaveLeader ==
    \* If there's at least one device not DOWN...
    (Cardinality({d \in DevicesSet : status[d] /= DOWN}) > 0)
    \* ...then eventually there should be at least one LEADER.
       ~> (Cardinality({d \in DevicesSet : status[d] = LEADER}) >= 1)

\* Specification definition for TLC checking
Spec == Init /\ [][Next]_vars /\ WF_vars(Next) \* Weak Fairness on vars is usually sufficient

\* Properties to check by TLC (can be put in .cfg or checked directly)
THEOREM Spec => []AtMostOneLeader
THEOREM Spec => []LeaderIsLowestActive
THEOREM Spec => []TypeOK
THEOREM Spec => EventuallyHaveLeader

=============================================================================
