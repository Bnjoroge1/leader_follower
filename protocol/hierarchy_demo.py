#!/usr/bin/env python3
"""
Hierarchical Neighborhood Demo
Demonstrates the hierarchical leader-follower protocol concepts
"""

import asyncio
import time
from hierarchy_classes import NeighborhoodManager, CouncilManager, NeighborhoodRole
from protocol_config import get_config_manager


class HierarchyDemo:
    """Demonstrates hierarchical neighborhood concepts"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.neighborhood_manager = NeighborhoodManager(strategy="hash", target_size=5)
        self.council_manager = CouncilManager(heartbeat_timeout=10.0)
        
    def demo_neighborhood_assignment(self, num_devices: int = 15):
        """Demonstrate how devices are assigned to neighborhoods"""
        print("🏘️  NEIGHBORHOOD ASSIGNMENT DEMO")
        print("=" * 50)
        
        print(f"Assigning {num_devices} devices to neighborhoods...")
        print(f"Target neighborhood size: {self.neighborhood_manager.target_size}")
        
        # Assign devices to neighborhoods
        assignments = {}
        for device_id in range(1, num_devices + 1):
            neighborhood_id = self.neighborhood_manager.assign_device_to_neighborhood(device_id)
            assignments[device_id] = neighborhood_id
        
        # Group by neighborhood
        neighborhoods = {}
        for device_id, neighborhood_id in assignments.items():
            if neighborhood_id not in neighborhoods:
                neighborhoods[neighborhood_id] = []
            neighborhoods[neighborhood_id].append(device_id)
        
        # Display results
        print(f"\n📍 NEIGHBORHOOD ASSIGNMENTS:")
        for neighborhood_id, devices in sorted(neighborhoods.items()):
            leader_id = min(devices)  # Lowest ID becomes leader
            print(f"   Neighborhood {neighborhood_id}: {len(devices)} devices")
            print(f"     Leader: Device {leader_id}")
            print(f"     Members: {sorted(devices)}")
        
        print(f"\n📊 STATISTICS:")
        print(f"   Total neighborhoods: {len(neighborhoods)}")
        print(f"   Average size: {num_devices / len(neighborhoods):.1f} devices")
        print(f"   Size range: {min(len(d) for d in neighborhoods.values())}-{max(len(d) for d in neighborhoods.values())} devices")
        
        return neighborhoods
    
    def demo_council_formation(self, neighborhoods):
        """Demonstrate council formation from neighborhood leaders"""
        print(f"\n🏛️  COUNCIL FORMATION DEMO")
        print("=" * 50)
        
        # Create council from neighborhood leaders
        leaders = []
        for neighborhood_id, devices in neighborhoods.items():
            leader_id = min(devices)  # Lowest ID becomes leader
            device_count = len(devices)
            
            # Add to council
            self.council_manager.add_member(leader_id, neighborhood_id, device_count)
            leaders.append((leader_id, neighborhood_id, device_count))
            
            print(f"   Leader {leader_id} (Neighborhood {neighborhood_id}, {device_count} devices) joined council")
        
        # Elect super leader
        super_leader_id = self.council_manager.get_super_leader()
        
        print(f"\n👑 SUPER LEADER ELECTION:")
        print(f"   Super Leader: Device {super_leader_id} (lowest ID among leaders)")
        
        # Show council structure
        print(f"\n🏛️  COUNCIL STRUCTURE:")
        for member in self.council_manager.get_active_members():
            role = "Super Leader + Neighborhood Leader" if member.leader_id == super_leader_id else "Neighborhood Leader"
            print(f"   Device {member.leader_id}: {role} (Neighborhood {member.neighborhood_id})")
        
        return super_leader_id, leaders
    
    def demo_message_flow(self, neighborhoods, super_leader_id):
        """Demonstrate message flow patterns in hierarchical system"""
        print(f"\n📨 MESSAGE FLOW DEMO")
        print("=" * 50)
        
        total_devices = sum(len(devices) for devices in neighborhoods.values())
        
        print(f"🔄 ATTENDANCE PATTERN (every 5 seconds):")
        attendance_messages = 0
        for neighborhood_id, devices in neighborhoods.items():
            leader_id = min(devices)
            local_messages = len(devices)  # Leader sends to each device in neighborhood
            attendance_messages += local_messages
            print(f"   Neighborhood {neighborhood_id}: Leader {leader_id} → {len(devices)} local devices ({local_messages} messages)")
        
        print(f"   Total attendance messages: {attendance_messages} (vs {total_devices * total_devices} in flat protocol)")
        
        print(f"\n🏛️  COUNCIL COORDINATION (every 30 seconds):")
        council_messages = len(neighborhoods) - 1  # All leaders report to super leader
        print(f"   Neighborhood leaders → Super Leader {super_leader_id}: {council_messages} summary messages")
        
        print(f"\n💬 TOTAL MESSAGE COMPARISON:")
        flat_messages = total_devices * total_devices  # Everyone to everyone
        hierarchical_messages = attendance_messages + council_messages
        reduction = ((flat_messages - hierarchical_messages) / flat_messages) * 100
        
        print(f"   Flat protocol: ~{flat_messages:,} messages per round")
        print(f"   Hierarchical: ~{hierarchical_messages:,} messages per round")
        print(f"   Reduction: {reduction:.1f}%")
        
        return attendance_messages, council_messages
    
    def demo_failure_scenarios(self, neighborhoods, super_leader_id):
        """Demonstrate failure handling in hierarchical system"""
        print(f"\n💥 FAILURE HANDLING DEMO")
        print("=" * 50)
        
        # Scenario 1: Regular device failure
        print(f"📍 SCENARIO 1: Regular device failure")
        neighborhood_0_devices = list(neighborhoods.values())[0]
        failed_device = max(neighborhood_0_devices)  # Not the leader
        leader_id = min(neighborhood_0_devices)
        
        print(f"   Device {failed_device} fails in neighborhood 0")
        print(f"   → Neighborhood Leader {leader_id} detects via SWIM/heartbeat")
        print(f"   → Leader removes device from local list")
        print(f"   → Leader reports updated count to Super Leader {super_leader_id}")
        print(f"   → Impact: Local to neighborhood only")
        
        # Scenario 2: Neighborhood leader failure
        print(f"\n📍 SCENARIO 2: Neighborhood leader failure")
        print(f"   Neighborhood Leader {leader_id} fails")
        print(f"   → Remaining devices in neighborhood 0 detect failure")
        print(f"   → Local election among remaining devices")
        print(f"   → New leader joins council")
        print(f"   → Super Leader updates council membership")
        print(f"   → Impact: Neighborhood-wide, council coordination")
        
        # Scenario 3: Super leader failure
        print(f"\n📍 SCENARIO 3: Super leader failure")
        print(f"   Super Leader {super_leader_id} fails")
        print(f"   → All neighborhood leaders detect timeout")
        print(f"   → Council election among remaining leaders")
        print(f"   → New super leader announces to all neighborhoods")
        print(f"   → Impact: System-wide, but neighborhoods continue operating")
        
        print(f"\n🎯 KEY BENEFITS:")
        print(f"   • Failures are contained to appropriate scope")
        print(f"   • Multiple levels of redundancy")
        print(f"   • System continues operating during leader transitions")
        print(f"   • No single point of failure")
    
    def demo_scalability_analysis(self):
        """Demonstrate scalability benefits"""
        print(f"\n📈 SCALABILITY ANALYSIS")
        print("=" * 50)
        
        device_counts = [50, 100, 500, 1000, 5000]
        target_size = 25
        
        print(f"Comparing message complexity (target neighborhood size: {target_size})")
        print(f"")
        print(f"{'Devices':>8} {'Flat O(N²)':>12} {'Hierarchical':>12} {'Reduction':>10}")
        print(f"{'-'*8} {'-'*12} {'-'*12} {'-'*10}")
        
        for n in device_counts:
            flat_messages = n * n
            num_neighborhoods = max(1, n // target_size)
            hierarchical_messages = n * target_size + num_neighborhoods * num_neighborhoods
            reduction = ((flat_messages - hierarchical_messages) / flat_messages) * 100
            
            print(f"{n:8,} {flat_messages:12,} {hierarchical_messages:12,} {reduction:9.1f}%")
        
        print(f"\n🎯 COMPLEXITY ANALYSIS:")
        print(f"   • Flat protocol: O(N²) - every device talks to every device")
        print(f"   • Hierarchical: O(N×k + m²) where k=neighborhood size, m=neighborhoods")
        print(f"   • For optimal k≈√N: Hierarchical ≈ O(N^1.5) vs Flat O(N²)")
        print(f"   • Memory per device: O(k) vs O(N)")
        print(f"   • Leadership load: Distributed across {num_neighborhoods} leaders vs 1")


async def run_complete_demo():
    """Run the complete hierarchical demonstration"""
    print("🚀 HIERARCHICAL LEADER-FOLLOWER PROTOCOL DEMONSTRATION")
    print("=" * 70)
    
    demo = HierarchyDemo()
    
    # Enable hierarchical configuration
    demo.config_manager.enable_hierarchy(True)
    demo.config_manager.update_hierarchy_config(
        neighborhood_strategy="hash",
        target_neighborhood_size=5,
        max_neighborhood_size=8,
        min_neighborhood_size=3
    )
    
    # Run demonstrations
    neighborhoods = demo.demo_neighborhood_assignment(15)
    super_leader_id, leaders = demo.demo_council_formation(neighborhoods)
    demo.demo_message_flow(neighborhoods, super_leader_id)
    demo.demo_failure_scenarios(neighborhoods, super_leader_id)
    demo.demo_scalability_analysis()
    
    print(f"\n✨ DEMONSTRATION COMPLETE!")
    print(f"   This shows how hierarchical neighborhoods improve scalability")
    print(f"   while maintaining the existing leader-follower protocol semantics.")
    print(f"   ")
    print(f"   To test with real devices:")
    print(f"   • python3 hierarchy_test_runner.py enable")
    print(f"   • python3 hierarchy_test_runner.py test --devices 20")
    print(f"   • python3 hierarchy_test_runner.py compare --devices 50")


if __name__ == "__main__":
    asyncio.run(run_complete_demo())
