import asyncio
import time
import random
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional, Tuple
from enum import Enum
from message_classes import Message, Action

class SwimMessageType(Enum):
    PING = "ping"
    ACK = "ack"
    PING_REQ = "ping_req"
    INDIRECT_PING = "indirect_ping"
    INDIRECT_ACK = "indirect_ack"
    ALIVE = "alive"
    SUSPECT = "suspect"
    CONFIRM = "confirm"
    GOSSIP = "gossip"

@dataclass
class SwimNode:
    """Represents a node in the SWIM membership list"""
    node_id: int
    state: str = "alive"  # alive, suspect, dead
    incarnation: int = 0
    last_seen: float = field(default_factory=time.time)
    suspect_timeout: float = 0.0
    
    def is_alive(self) -> bool:
        return self.state == "alive"
    
    def is_suspect(self) -> bool:
        return self.state == "suspect"
    
    def is_dead(self) -> bool:
        return self.state == "dead"

@dataclass
class SwimMessage:
    """SWIM protocol message structure"""
    msg_type: SwimMessageType
    sender_id: int
    target_id: int
    incarnation: int = 0
    gossip_data: List[Tuple[int, str, int]] = field(default_factory=list)  # (node_id, state, incarnation)
    sequence_num: int = 0
    timestamp: float = field(default_factory=time.time)
    
    def to_payload(self) -> int:
        """Convert SWIM message to integer payload for transmission"""
        # Encode message type, sender, target, incarnation into integer
        # Format: [msg_type(2)][sender_id(4)][target_id(4)][incarnation(2)]
        msg_type_code = list(SwimMessageType).index(self.msg_type)
        payload = (msg_type_code * 10**10 + 
                  self.sender_id * 10**6 + 
                  self.target_id * 10**2 + 
                  self.incarnation)
        return payload
    
    @classmethod
    def from_payload(cls, payload: int, sender_id: int) -> 'SwimMessage':
        """Decode integer payload back to SWIM message"""
        msg_type_code = payload // 10**10
        remainder = payload % 10**10
        decoded_sender = remainder // 10**6
        remainder = remainder % 10**6
        target_id = remainder // 10**2
        incarnation = remainder % 10**2
        
        msg_type = list(SwimMessageType)[msg_type_code]
        return cls(
            msg_type=msg_type,
            sender_id=decoded_sender,
            target_id=target_id,
            incarnation=incarnation
        )

class SwimProtocol:
    """SWIM failure detection and membership protocol implementation"""
    
    def __init__(self, node_id: int, transceiver, metrics_collector):
        self.node_id = node_id
        self.transceiver = transceiver
        self.metrics_collector = metrics_collector
        
        # SWIM parameters (configurable)
        self.protocol_period = 1.0  # Time between protocol rounds
        self.ack_timeout = 0.5  # Time to wait for ACK
        self.suspect_timeout = 3.0  # Time before suspect becomes dead
        self.indirect_ping_nodes = 3  # Number of nodes for indirect ping
        self.gossip_fanout = 3  # Number of nodes to gossip to
        self.max_gossip_per_message = 5  # Max gossip entries per message
        
        # Membership state
        self.membership: Dict[int, SwimNode] = {}
        self.local_incarnation = 0
        
        # Protocol state
        self.ping_requests: Dict[int, float] = {}  # node_id -> request_time
        self.indirect_ping_requests: Dict[int, Set[int]] = {}  # target -> set of intermediaries
        self.gossip_queue: List[Tuple[int, str, int]] = []  # (node_id, state, incarnation)
        
        # Statistics
        self.round_count = 0
        self.failed_pings = 0
        self.successful_pings = 0
        
        # Task management
        self.protocol_task: Optional[asyncio.Task] = None
        self.running = False
        
    def add_node(self, node_id: int):
        """Add a new node to the membership list"""
        if node_id not in self.membership and node_id != self.node_id:
            self.membership[node_id] = SwimNode(node_id=node_id)
            print(f"SWIM: Added node {node_id} to membership")
            
    def remove_node(self, node_id: int):
        """Remove a node from membership list"""
        if node_id in self.membership:
            del self.membership[node_id]
            print(f"SWIM: Removed node {node_id} from membership")
            
    def get_alive_nodes(self) -> List[int]:
        """Get list of alive node IDs"""
        return [node_id for node_id, node in self.membership.items() if node.is_alive()]
    
    def get_random_alive_node(self) -> Optional[int]:
        """Select a random alive node for ping"""
        alive_nodes = self.get_alive_nodes()
        return random.choice(alive_nodes) if alive_nodes else None
    
    def get_random_nodes(self, exclude: Set[int], count: int) -> List[int]:
        """Get random nodes excluding specified ones"""
        available = [nid for nid in self.membership.keys() 
                    if nid not in exclude and self.membership[nid].is_alive()]
        return random.sample(available, min(count, len(available)))
    
    async def start(self):
        """Start the SWIM protocol"""
        if self.running:
            return
            
        self.running = True
        self.protocol_task = asyncio.create_task(self._protocol_loop())
        print(f"SWIM: Started protocol for node {self.node_id}")
        
    async def stop(self):
        """Stop the SWIM protocol"""
        self.running = False
        if self.protocol_task:
            self.protocol_task.cancel()
            try:
                await self.protocol_task
            except asyncio.CancelledError:
                pass
        print(f"SWIM: Stopped protocol for node {self.node_id}")
        
    async def _protocol_loop(self):
        """Main SWIM protocol loop"""
        try:
            while self.running:
                start_time = time.time()
                
                # Execute one round of SWIM protocol
                await self._execute_round()
                
                # Update metrics
                self.metrics_collector.update_protocol_specific_metrics(
                    self.node_id,
                    gossip_fanout=self.gossip_fanout,
                    ping_timeout=self.ack_timeout
                )
                
                # Wait for next round
                elapsed = time.time() - start_time
                sleep_time = max(0, self.protocol_period - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    
        except asyncio.CancelledError:
            print(f"SWIM: Protocol loop cancelled for node {self.node_id}")
        except Exception as e:
            print(f"SWIM: Error in protocol loop for node {self.node_id}: {e}")
            
    async def _execute_round(self):
        """Execute one round of the SWIM protocol"""
        self.round_count += 1
        
        # 1. Select a random node to ping
        target_node = self.get_random_alive_node()
        if target_node is None:
            return  # No nodes to ping
        
        # 2. Send ping and wait for ACK
        ping_successful = await self._ping_node(target_node)
        
        if not ping_successful:
            # 3. If no ACK, try indirect ping through other nodes
            indirect_successful = await self._indirect_ping(target_node)
            
            if not indirect_successful:
                # 4. Mark node as suspect
                await self._mark_suspect(target_node)
        
        # 5. Handle suspect timeouts
        await self._handle_suspect_timeouts()
        
        # 6. Gossip membership updates
        await self._gossip_membership()
        
    async def _ping_node(self, target_id: int) -> bool:
        """Send ping to target node and wait for ACK"""
        ping_msg = SwimMessage(
            msg_type=SwimMessageType.PING,
            sender_id=self.node_id,
            target_id=target_id,
            incarnation=self.local_incarnation
        )
        
        # Send ping
        await self._send_swim_message(ping_msg)
        self.ping_requests[target_id] = time.time()
        
        # Wait for ACK
        ack_received = await self._wait_for_ack(target_id, self.ack_timeout)
        
        if ack_received:
            self.successful_pings += 1
            # Update node as alive
            if target_id in self.membership:
                self.membership[target_id].state = "alive"
                self.membership[target_id].last_seen = time.time()
            return True
        else:
            self.failed_pings += 1
            return False
            
    async def _indirect_ping(self, target_id: int) -> bool:
        """Perform indirect ping through intermediate nodes"""
        # Select random intermediate nodes
        intermediaries = self.get_random_nodes(
            exclude={target_id, self.node_id}, 
            count=self.indirect_ping_nodes
        )
        
        if not intermediaries:
            return False
        
        self.indirect_ping_requests[target_id] = set(intermediaries)
        
        # Send ping-req to intermediaries
        for intermediary in intermediaries:
            ping_req_msg = SwimMessage(
                msg_type=SwimMessageType.PING_REQ,
                sender_id=self.node_id,
                target_id=intermediary,
                incarnation=self.local_incarnation
            )
            # Include target in gossip data for ping-req
            ping_req_msg.gossip_data = [(target_id, "ping_target", 0)]
            await self._send_swim_message(ping_req_msg)
        
        # Wait for indirect ACKs
        return await self._wait_for_indirect_ack(target_id, self.ack_timeout)
        
    async def _mark_suspect(self, node_id: int):
        """Mark a node as suspect"""
        if node_id in self.membership:
            node = self.membership[node_id]
            if node.state == "alive":
                node.state = "suspect"
                node.suspect_timeout = time.time() + self.suspect_timeout
                
                # Add to gossip queue
                self.gossip_queue.append((node_id, "suspect", node.incarnation))
                
                # Record failure detection
                detection_time = time.time() - self.ping_requests.get(node_id, time.time())
                self.metrics_collector.record_failure_detection(
                    self.node_id, node_id, detection_time, True
                )
                
                print(f"SWIM: Marked node {node_id} as suspect")
                
    async def _handle_suspect_timeouts(self):
        """Handle nodes that have been suspect for too long"""
        current_time = time.time()
        nodes_to_confirm = []
        
        for node_id, node in self.membership.items():
            if node.is_suspect() and current_time > node.suspect_timeout:
                nodes_to_confirm.append(node_id)
        
        for node_id in nodes_to_confirm:
            await self._confirm_dead(node_id)
            
    async def _confirm_dead(self, node_id: int):
        """Confirm a node as dead and remove from membership"""
        if node_id in self.membership:
            self.membership[node_id].state = "dead"
            
            # Add to gossip queue
            self.gossip_queue.append((node_id, "dead", self.membership[node_id].incarnation))
            
            # Record node failure
            self.metrics_collector.record_node_failure(node_id)
            
            print(f"SWIM: Confirmed node {node_id} as dead")
            
            # Remove from membership after a delay to allow gossip propagation
            asyncio.create_task(self._delayed_removal(node_id))
            
    async def _delayed_removal(self, node_id: int):
        """Remove dead node after delay"""
        await asyncio.sleep(self.protocol_period * 3)  # Wait 3 rounds
        if node_id in self.membership and self.membership[node_id].is_dead():
            del self.membership[node_id]
            print(f"SWIM: Removed dead node {node_id} from membership")
            
    async def _gossip_membership(self):
        """Gossip membership updates to random nodes"""
        if not self.gossip_queue:
            return
            
        # Select random nodes for gossip
        gossip_targets = self.get_random_nodes(
            exclude={self.node_id}, 
            count=self.gossip_fanout
        )
        
        for target in gossip_targets:
            # Prepare gossip data (up to max_gossip_per_message entries)
            gossip_data = self.gossip_queue[:self.max_gossip_per_message]
            
            gossip_msg = SwimMessage(
                msg_type=SwimMessageType.GOSSIP,
                sender_id=self.node_id,
                target_id=target,
                incarnation=self.local_incarnation,
                gossip_data=gossip_data
            )
            
            await self._send_swim_message(gossip_msg)
        
        # Age out old gossip entries
        self.gossip_queue = self.gossip_queue[self.max_gossip_per_message:]
        
    async def _send_swim_message(self, swim_msg: SwimMessage):
        """Send a SWIM message through the transceiver"""
        # Convert SWIM message to standard message format
        msg = Message(
            action=Action.SWIM_MESSAGE.value,  # We'll need to add this to Action enum
            payload=swim_msg.to_payload(),
            leader_id=self.node_id,
            follower_id=swim_msg.target_id
        )
        
        # Track metrics
        message_id = f"swim_{self.node_id}_{swim_msg.sequence_num}_{int(time.time() * 1000)}"
        message_size = len(str(msg.msg))
        self.metrics_collector.record_message_sent(self.node_id, message_id, message_size)
        
        await self.transceiver.async_send(msg.msg)
        
    async def _wait_for_ack(self, target_id: int, timeout: float) -> bool:
        """Wait for ACK from target node"""
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            # Check for incoming ACK (this would be handled by message processing)
            if target_id not in self.ping_requests:
                return True  # ACK received
            await asyncio.sleep(0.01)  # Small sleep to prevent busy waiting
            
        # Cleanup ping request
        self.ping_requests.pop(target_id, None)
        return False
        
    async def _wait_for_indirect_ack(self, target_id: int, timeout: float) -> bool:
        """Wait for indirect ACK from intermediary nodes"""
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            if target_id not in self.indirect_ping_requests:
                return True  # Indirect ACK received
            await asyncio.sleep(0.01)
            
        # Cleanup indirect ping request
        self.indirect_ping_requests.pop(target_id, None)
        return False
        
    async def handle_swim_message(self, swim_msg: SwimMessage):
        """Handle incoming SWIM message"""
        if swim_msg.msg_type == SwimMessageType.PING:
            await self._handle_ping(swim_msg)
        elif swim_msg.msg_type == SwimMessageType.ACK:
            await self._handle_ack(swim_msg)
        elif swim_msg.msg_type == SwimMessageType.PING_REQ:
            await self._handle_ping_req(swim_msg)
        elif swim_msg.msg_type == SwimMessageType.INDIRECT_PING:
            await self._handle_indirect_ping(swim_msg)
        elif swim_msg.msg_type == SwimMessageType.INDIRECT_ACK:
            await self._handle_indirect_ack(swim_msg)
        elif swim_msg.msg_type == SwimMessageType.GOSSIP:
            await self._handle_gossip(swim_msg)
            
    async def _handle_ping(self, swim_msg: SwimMessage):
        """Handle incoming PING message"""
        # Send ACK back
        ack_msg = SwimMessage(
            msg_type=SwimMessageType.ACK,
            sender_id=self.node_id,
            target_id=swim_msg.sender_id,
            incarnation=self.local_incarnation
        )
        await self._send_swim_message(ack_msg)
        
        # Update membership info
        self.add_node(swim_msg.sender_id)
        
    async def _handle_ack(self, swim_msg: SwimMessage):
        """Handle incoming ACK message"""
        # Remove from pending ping requests
        self.ping_requests.pop(swim_msg.sender_id, None)
        
        # Update membership
        if swim_msg.sender_id in self.membership:
            self.membership[swim_msg.sender_id].last_seen = time.time()
            self.membership[swim_msg.sender_id].state = "alive"
            
    async def _handle_ping_req(self, swim_msg: SwimMessage):
        """Handle PING-REQ message (request to ping another node)"""
        if swim_msg.gossip_data:
            target_id = swim_msg.gossip_data[0][0]  # Extract target from gossip data
            
            # Send indirect ping to target
            indirect_ping_msg = SwimMessage(
                msg_type=SwimMessageType.INDIRECT_PING,
                sender_id=self.node_id,
                target_id=target_id,
                incarnation=self.local_incarnation
            )
            await self._send_swim_message(indirect_ping_msg)
            
    async def _handle_indirect_ping(self, swim_msg: SwimMessage):
        """Handle indirect PING message"""
        # Send indirect ACK back to original requester
        # (This would need more complex routing logic in a real implementation)
        pass
        
    async def _handle_indirect_ack(self, swim_msg: SwimMessage):
        """Handle indirect ACK message"""
        # Remove from indirect ping requests
        for target_id, intermediaries in list(self.indirect_ping_requests.items()):
            if swim_msg.sender_id in intermediaries:
                self.indirect_ping_requests.pop(target_id, None)
                break
                
    async def _handle_gossip(self, swim_msg: SwimMessage):
        """Handle gossip message with membership updates"""
        for node_id, state, incarnation in swim_msg.gossip_data:
            if node_id == self.node_id:
                continue  # Ignore gossip about self
                
            if node_id not in self.membership:
                self.add_node(node_id)
                
            node = self.membership[node_id]
            
            # Update node state based on gossip (with incarnation number logic)
            if incarnation > node.incarnation or (incarnation == node.incarnation and state == "dead"):
                node.state = state
                node.incarnation = incarnation
                node.last_seen = time.time()
                
                if state == "dead":
                    self.metrics_collector.record_node_failure(node_id)
                elif state == "alive":
                    self.metrics_collector.record_node_recovery(node_id)
                    
    def get_membership_status(self) -> Dict[str, any]:
        """Get current membership status for monitoring"""
        return {
            'total_nodes': len(self.membership),
            'alive_nodes': len([n for n in self.membership.values() if n.is_alive()]),
            'suspect_nodes': len([n for n in self.membership.values() if n.is_suspect()]),
            'dead_nodes': len([n for n in self.membership.values() if n.is_dead()]),
            'round_count': self.round_count,
            'successful_pings': self.successful_pings,
            'failed_pings': self.failed_pings,
            'ping_success_rate': self.successful_pings / max(1, self.successful_pings + self.failed_pings)
        } 