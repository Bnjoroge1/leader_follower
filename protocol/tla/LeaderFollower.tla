---- MODULE LeaderFollower ----
EXTENDS Naturals, FiniteSets, Sequences

CONSTANTS MaxDevices

VARIABLES 
    devices,    \* Set of devices in the network
    leader,     \* The current leader device (or NULL if no leader)
    status,     \* Function mapping devices to their status (JOINING, FOLLOWER, LEADER)
    network,    \* Set of devices that have joined the network
    messages    \* Messages in transit

vars == <<devices, leader, status, network, messages>>

NULL == 0  \* Represents no leader

\* Status values
JOINING  == "JOINING"
FOLLOWER == "FOLLOWER"
LEADER   == "LEADER"

\* Message types
ATTENDANCE == "ATTENDANCE"
LEADER_CLAIM == "LEADER_CLAIM"
CHECK_IN == "CHECK_IN"
CHECK_IN_RESPONSE == "CHECK_IN_RESPONSE"

\* Initial state
Init ==
    /\ devices = {}
    /\ leader = NULL
    /\ status = [d \in 1..MaxDevices |-> JOINING]
    /\ network = {}
    /\ messages = <<>>

\* Add a new device to the system
AddDevice ==
    /\ Cardinality(devices) < MaxDevices
    /\ \E d \in (1..MaxDevices) \ devices:
        /\ devices' = devices \union {d}
        /\ status' = [status EXCEPT ![d] = JOINING]
        /\ UNCHANGED <<leader, network, messages>>

\* Device joins the network
JoinNetwork ==
    /\ \E d \in devices:
        /\ status[d] = JOINING
        /\ network' = network \union {d}
        /\ status' = [status EXCEPT ![d] = FOLLOWER]
        /\ messages' = Append(messages, [type |-> ATTENDANCE, from |-> d])
        /\ UNCHANGED <<devices, leader>>

\* Select initial leader
SelectInitialLeader ==
    /\ leader = NULL
    /\ network /= {}
    /\ \E d \in network:
        /\ leader' = d
        /\ status' = [status EXCEPT ![d] = LEADER]
        /\ messages' = Append(messages, [type |-> LEADER_CLAIM, from |-> d])
        /\ UNCHANGED <<devices, network>>

\* Handle leader claim message
HandleLeaderClaim ==
    /\ messages /= <<>>
    /\ \E i \in DOMAIN messages:
        /\ messages[i].type = LEADER_CLAIM
        /\ leader' = messages[i].from
        /\ status' = [d \in DOMAIN status |->
                        IF d = messages[i].from THEN LEADER
                        ELSE IF status[d] /= JOINING THEN FOLLOWER
                        ELSE status[d]]
        /\ messages' = SubSeq(messages, 1, i-1) \o SubSeq(messages, i+1, Len(messages))
        /\ UNCHANGED <<devices, network>>

\* Leader sends check-in messages to followers
LeaderCheckIn ==
    /\ leader /= NULL
    /\ \E d \in network:
        /\ d /= leader
        /\ messages' = Append(messages, [type |-> CHECK_IN, from |-> leader, to |-> d])
        /\ UNCHANGED <<devices, leader, status, network>>

\* Follower responds to check-in
FollowerRespond ==
    /\ messages /= <<>>
    /\ \E i \in DOMAIN messages:
        /\ messages[i].type = CHECK_IN
        /\ messages' = SubSeq(messages, 1, i-1) \o 
                      SubSeq(messages, i+1, Len(messages)) \o
                      <<[type |-> CHECK_IN_RESPONSE, 
                         from |-> messages[i].to, 
                         to |-> messages[i].from]>>
        /\ UNCHANGED <<devices, leader, status, network>>

\* Leader processes check-in responses
ProcessCheckInResponse ==
    /\ messages /= <<>>
    /\ \E i \in DOMAIN messages:
        /\ messages[i].type = CHECK_IN_RESPONSE
        /\ messages' = SubSeq(messages, 1, i-1) \o SubSeq(messages, i+1, Len(messages))
        /\ UNCHANGED <<devices, leader, status, network>>

\* Next state
Next ==
    \/ AddDevice
    \/ JoinNetwork
    \/ SelectInitialLeader
    \/ HandleLeaderClaim
    \/ LeaderCheckIn
    \/ FollowerRespond
    \/ ProcessCheckInResponse

\* Invariants
AtMostOneLeader == 
    Cardinality({d \in devices : status[d] = LEADER}) <= 1

EventuallyHaveLeader == 
    <>(leader /= NULL)

AllDevicesEventuallyJoin == 
    [](Cardinality(devices) > 0 => <>(network = devices))

\* Specification
Spec == Init /\ [][Next]_vars /\ WF_vars(Next)

\* Properties to check
THEOREM Spec => []AtMostOneLeader
THEOREM Spec => EventuallyHaveLeader
THEOREM Spec => AllDevicesEventuallyJoin

====