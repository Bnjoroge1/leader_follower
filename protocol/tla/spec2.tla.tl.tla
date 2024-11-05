---- MODULE LeaderFollower ----
EXTENDS Naturals, TLC

CONSTANTS N \* Number of nodes

VARIABLES 
    nodes, \* A mapping from node IDs to their states (e.g., "leader", "follower", "candidate")
    leader, \* The current leader node ID
    channels \* A mapping representing the network topology (which nodes are connected)

\* Initial state of the system
Init == 
    /\ nodes = [i \in 1..N |-> "follower"] \* Initially, all nodes are followers
    /\ leader = 0 \* No leader initially
    /\ channels = [i \in 1..N, j \in 1..N |-> IF i /= j THEN TRUE ELSE FALSE] \* Fully connected mesh

\* Action: Leader Election
LeaderElection ==
    /\ \E i \in 1..N: nodes[i] = "candidate" \* A candidate node is available
    /\ leader' = i \* Elect this node as the leader
    /\ nodes' = [j \in 1..N |-> IF j = i THEN "leader" ELSE "follower"] \* Update node states

\* Action: Message Passing
MessagePassing ==
    /\ \E i, j \in 1..N: channels[i][j] \* There is a channel between nodes i and j
    /\ \E msg \in {"attendance", "check-in", "d_list"}: TRUE \* Simulate message types
    /\ UNCHANGED <<nodes, leader>> \* No state change, just message passing

\* Network Topology: Fully connected mesh
NetworkTopology ==
    /\ \A i, j \in 1..N: channels[i][j] = TRUE \* All nodes are interconnected

\* Next-state relation
Next ==
    \/ LeaderElection
    \/ MessagePassing

\* Specification
Spec == Init /\ [][Next]_<<nodes, leader, channels>>

\* Invariants and properties can be added later
===============================
