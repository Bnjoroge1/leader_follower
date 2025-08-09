"""
Hierarchical neighborhood data structures and utilities
"""

MAX_SIZE = 30
MIN_SIZE = 20
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional, Tuple
from enum import Enum


class NeighborhoodRole(Enum):
    """Role of a device in the hierarchical system"""
    DEVICE = "device"
    NEIGHBORHOOD_LEADER = "neighborhood_leader"
    SUPER_LEADER = "super_leader"


@dataclass
class NeighborhoodInfo:
    """Information about a neighborhood"""
    neighborhood_id: int
    leader_id: Optional[int] = None
    device_count: int = 0
    last_summary_time: float = field(default_factory=time.time)
    is_active: bool = True
    
    def update_summary(self, leader_id: int, device_count: int):
        """Update neighborhood summary information"""
        self.leader_id = leader_id
        self.device_count = device_count
        self.last_summary_time = time.time()
        self.is_active = True


@dataclass
class CouncilMember:
    """Information about a council member (neighborhood leader)"""
    leader_id: int
    neighborhood_id: int
    last_heartbeat: float = field(default_factory=time.time)
    device_count: int = 0
    is_active: bool = True
    
    def update_heartbeat(self):
        """Update last heartbeat time"""
        self.last_heartbeat = time.time()
        self.is_active = True
    
    def is_alive(self, timeout: float) -> bool:
        """Check if council member is still alive based on timeout"""
        return time.time() - self.last_heartbeat < timeout


class NeighborhoodManager:
    """Manages neighborhood assignments and operations"""
    
    def __init__(self, strategy: str = "hash", target_size: int = 25):
        self.strategy = strategy
        self.target_size = target_size
        self.neighborhoods: Dict[int, NeighborhoodInfo] = {}
        self.device_assignments: Dict[int, int] = {}  # device_id -> neighborhood_id
        
    def compute_neighborhood_id(self, device_id: int, total_neighborhoods: int = None) -> int:
        """Compute neighborhood ID for a device based on strategy"""
        if self.strategy == "hash":
            # Use consistent hashing based on device ID
            hash_obj = hashlib.md5(str(device_id).encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            
            if total_neighborhoods is None:
                # Use a fixed calculation based on a reasonable estimate
                # For testing with ~20 devices and target_size=8, use 3 neighborhoods
                total_neighborhoods = max(1, 3)  # Fixed for now, should be configurable
            
            return hash_int % total_neighborhoods
            
        elif self.strategy == "geographic":
            # Placeholder for geographic-based assignment
            # In real implementation, this would use device location
            return device_id % max(1, len(self.device_assignments) // self.target_size + 1)
            
        elif self.strategy == "manual":
            # Manual assignment - would be set externally
            return self.device_assignments.get(device_id, 0)
            
        else:
            # Default to hash strategy
            return self.compute_neighborhood_id(device_id, total_neighborhoods)
    
    def assign_device_to_neighborhood(self, device_id: int, neighborhood_id: int = None) -> int:
        """Assign a device to a neighborhood"""
        if neighborhood_id is None:
            neighborhood_id = self.compute_neighborhood_id(device_id)
        
        self.device_assignments[device_id] = neighborhood_id
        
        # Update neighborhood info
        if neighborhood_id not in self.neighborhoods:
            self.neighborhoods[neighborhood_id] = NeighborhoodInfo(neighborhood_id)
        
        return neighborhood_id
    
    def remove_device_from_neighborhood(self, device_id: int):
        """Remove a device from its neighborhood"""
        if device_id in self.device_assignments:
            neighborhood_id = self.device_assignments[device_id]
            del self.device_assignments[device_id]
            
            # Update neighborhood device count
            if neighborhood_id in self.neighborhoods:
                remaining_devices = sum(1 for nid in self.device_assignments.values() 
                                      if nid == neighborhood_id)
                self.neighborhoods[neighborhood_id].device_count = remaining_devices
    def move_device_neighborhood(self, device_id: int, incoming_neighborhood_id: int) -> None:
        '''move device from one neighborhood to the other.'''
        outgoing_neighborhood = self.get_device_neighborhood(device_id=device_id)
        self.remove_device_from_neighborhood(device_id=device_id)
        self.assign_device_to_neighborhood(outgoing_neighborhood)

    def get_device_neighborhood(self, device_id: int) -> Optional[int]:
        """Get the neighborhood ID for a device"""
        return self.device_assignments.get(device_id)
    
    def get_neighborhood_devices(self, neighborhood_id: int) -> List[int]:
        """Get all devices in a neighborhood"""
        return [device_id for device_id, nid in self.device_assignments.items() 
                if nid == neighborhood_id]
    
    def get_neighborhood_info(self, neighborhood_id: int) -> Optional[NeighborhoodInfo]:
        """Get information about a neighborhood"""
        return self.neighborhoods.get(neighborhood_id)
    
    def update_neighborhood_leader(self, neighborhood_id: int, leader_id: int, device_count: int):
        """Update neighborhood leader and device count"""
        if neighborhood_id not in self.neighborhoods:
            self.neighborhoods[neighborhood_id] = NeighborhoodInfo(neighborhood_id)
        
        self.neighborhoods[neighborhood_id].update_summary(leader_id, device_count)
    
    def should_split_neighborhood(self, neighborhood_id: int, max_size: int = MAX_SIZE) -> bool:
        """Check if a neighborhood should be split"""
        info = self.neighborhoods.get(neighborhood_id)
        if not info:
            return False
        
        return info.device_count > max_size
    
    def should_merge_neighborhood(self, neighborhood_id: int, min_size: int = MIN_SIZE) -> bool:
        """Check if a neighborhood should be merged"""
        info = self.neighborhoods.get(neighborhood_id)
        if not info:
            return False
        
        return info.device_count < min_size
    
    def get_active_neighborhoods(self) -> List[int]:
        """Get list of active neighborhood IDs"""
        return [nid for nid, info in self.neighborhoods.items() if info.is_active]


class CouncilManager:
    """Manages the council of neighborhood leaders"""
    
    def __init__(self, heartbeat_timeout: float = 30.0):
        self.heartbeat_timeout = heartbeat_timeout
        self.members: Dict[int, CouncilMember] = {}  # leader_id -> CouncilMember
        self.super_leader_id: Optional[int] = None
        self.last_election_time: float = 0
        
    def add_member(self, leader_id: int, neighborhood_id: int, device_count: int = 0):
        """Add a new council member"""
        self.members[leader_id] = CouncilMember(
            leader_id=leader_id,
            neighborhood_id=neighborhood_id,
            device_count=device_count
        )
        
        # Trigger super-leader election if needed
        if self.super_leader_id is None or self.super_leader_id not in self.members:
            self._elect_super_leader()
    
    def remove_member(self, leader_id: int):
        """Remove a council member"""
        if leader_id in self.members:
            del self.members[leader_id]
            
            # Re-elect super-leader if the current one was removed
            if self.super_leader_id == leader_id:
                self.super_leader_id = None
                self._elect_super_leader()
    
    def update_member_heartbeat(self, leader_id: int):
        """Update heartbeat for a council member"""
        if leader_id in self.members:
            self.members[leader_id].update_heartbeat()
    
    def update_member_summary(self, leader_id: int, device_count: int):
        """Update summary information for a council member"""
        if leader_id in self.members:
            self.members[leader_id].device_count = device_count
            self.members[leader_id].update_heartbeat()
    
    def check_member_timeouts(self) -> List[int]:
        """Check for timed-out members and return their IDs"""
        timed_out = []
        current_time = time.time()
        
        for leader_id, member in list(self.members.items()):
            if not member.is_alive(self.heartbeat_timeout):
                member.is_active = False
                timed_out.append(leader_id)
                
                # Remove inactive members after timeout
                if current_time - member.last_heartbeat > self.heartbeat_timeout * 2:
                    self.remove_member(leader_id)
        
        return timed_out
    
    def _elect_super_leader(self):
        """Elect a new super-leader from active council members"""
        active_members = [member for member in self.members.values() if member.is_active]
        
        if not active_members:
            self.super_leader_id = None
            return
        
        # Use lowest ID as tiebreaker (same as existing election logic)
        new_super_leader = min(active_members, key=lambda m: m.leader_id)
        self.super_leader_id = new_super_leader.leader_id
        self.last_election_time = time.time()
        
        print(f"Council elected new super-leader: {self.super_leader_id}")
    
    def get_super_leader(self) -> Optional[int]:
        """Get the current super-leader ID"""
        # Check if current super-leader is still active
        if (self.super_leader_id and 
            self.super_leader_id in self.members and 
            self.members[self.super_leader_id].is_active):
            return self.super_leader_id
        
        # Re-elect if current super-leader is inactive
        self._elect_super_leader()
        return self.super_leader_id
    
    def get_active_members(self) -> List[CouncilMember]:
        """Get list of active council members"""
        return [member for member in self.members.values() if member.is_active]
    
    def get_member_count(self) -> int:
        """Get count of active council members"""
        return len(self.get_active_members())
    
    def is_super_leader(self, leader_id: int) -> bool:
        """Check if a leader is the current super-leader"""
        return self.get_super_leader() == leader_id


def encode_neighborhood_payload(neighborhood_id: int, data: int = 0) -> int:
    """Encode neighborhood ID and data into message payload"""
    # Format: [neighborhood_id(4 digits)][data(4 digits)]
    return neighborhood_id * 10000 + (data % 10000)


def decode_neighborhood_payload(payload: int) -> Tuple[int, int]:
    """Decode neighborhood ID and data from message payload"""
    neighborhood_id = payload // 10000
    data = payload % 10000
    return neighborhood_id, data


def encode_council_payload(member_count: int, neighborhood_id: int) -> int:
    """Encode council summary data into message payload"""
    # Format: [member_count(4 digits)][neighborhood_id(4 digits)]
    return member_count * 10000 + neighborhood_id


def decode_council_payload(payload: int) -> Tuple[int, int]:
    """Decode council summary data from message payload"""
    member_count = payload // 10000
    neighborhood_id = payload % 10000
    return member_count, neighborhood_id
