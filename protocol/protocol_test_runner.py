#!/usr/bin/env python3
"""
Protocol Test Runner - CLI tool for testing and comparing heartbeat vs SWIM protocols
"""

import argparse
import asyncio
import time
from pathlib import Path
from typing import List
import sys

from protocol_config import get_config_manager, switch_protocol
from metrics_collector import get_metrics_collector, initialize_metrics_collection
from protocol_analyzer import run_protocol_comparison
from simulation_network import Network, SimulationNode, SimulationTransceiver
from device_classes import ThisDevice

class ProtocolTestRunner:
    """Runs automated tests comparing heartbeat and SWIM protocols"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.config_manager = get_config_manager()
        
    async def run_heartbeat_test(self, num_nodes: int = 5, duration: int = 60) -> str:
        """Run a test with heartbeat protocol"""
        print(f"Running heartbeat test with {num_nodes} nodes for {duration} seconds...")
        
        # Switch to heartbeat protocol
        switch_protocol("heartbeat")
        
        # Initialize metrics collection
        metrics_collector = initialize_metrics_collection(self.output_dir)
        
        # Create network and nodes
        network = Network()
        nodes = []
        
        for i in range(num_nodes):
            node = SimulationNode(
                node_id=i + 1,
                active_value=1,
                checkpoint_mgr=None
            )
            nodes.append(node)
            network.add_node(i + 1, node)
        
        # Create full mesh network topology
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                network.create_channel(i + 1, j + 1)
        
        try:
            # Start all nodes
            for node in nodes:
                await node.start()
            
            # Let the test run
            start_time = time.time()
            while time.time() - start_time < duration:
                # Periodically snapshot metrics
                metrics_collector.snapshot_metrics()
                
                # Simulate some failures halfway through
                if time.time() - start_time > duration / 2 and len(nodes) > 2:
                    # Simulate node failure
                    failed_node = nodes[-1]
                    print(f"Simulating failure of node {failed_node.node_id}")
                    metrics_collector.record_node_failure(failed_node.node_id)
                    await failed_node.stop()
                    nodes.remove(failed_node)
                
                await asyncio.sleep(5)  # Snapshot every 5 seconds
            
        finally:
            # Stop all remaining nodes
            for node in nodes:
                await node.stop()
        
        # Export metrics
        metrics_file = f"heartbeat_metrics_{int(time.time())}.json"
        metrics_collector.export_metrics(metrics_file)
        print(f"Heartbeat test completed. Metrics saved to {metrics_file}")
        
        return metrics_file
    
    async def run_swim_test(self, num_nodes: int = 5, duration: int = 60) -> str:
        """Run a test with SWIM protocol"""
        print(f"Running SWIM test with {num_nodes} nodes for {duration} seconds...")
        
        # Switch to SWIM protocol
        switch_protocol("swim")
        
        # Initialize metrics collection
        metrics_collector = initialize_metrics_collection(self.output_dir)
        
        # Create network and nodes
        network = Network()
        nodes = []
        
        for i in range(num_nodes):
            node = SimulationNode(
                node_id=i + 1,
                active_value=1,
                checkpoint_mgr=None
            )
            nodes.append(node)
            network.add_node(i + 1, node)
        
        # Create full mesh network topology
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                network.create_channel(i + 1, j + 1)
        
        try:
            # Start all nodes
            for node in nodes:
                await node.start()
            
            # Let the test run
            start_time = time.time()
            while time.time() - start_time < duration:
                # Periodically snapshot metrics
                metrics_collector.snapshot_metrics()
                
                # Simulate some failures halfway through
                if time.time() - start_time > duration / 2 and len(nodes) > 2:
                    # Simulate node failure
                    failed_node = nodes[-1]
                    print(f"Simulating failure of node {failed_node.node_id}")
                    metrics_collector.record_node_failure(failed_node.node_id)
                    await failed_node.stop()
                    nodes.remove(failed_node)
                
                await asyncio.sleep(5)  # Snapshot every 5 seconds
            
        finally:
            # Stop all remaining nodes
            for node in nodes:
                await node.stop()
        
        # Export metrics
        metrics_file = f"swim_metrics_{int(time.time())}.json"
        metrics_collector.export_metrics(metrics_file)
        print(f"SWIM test completed. Metrics saved to {metrics_file}")
        
        return metrics_file
    
    async def run_comparison_test(self, num_nodes: int = 5, duration: int = 60):
        """Run both protocols and generate comparison"""
        print("Starting comprehensive protocol comparison...")
        
        # Run heartbeat test
        heartbeat_file = await self.run_heartbeat_test(num_nodes, duration)
        
        # Wait a bit between tests
        await asyncio.sleep(5)
        
        # Run SWIM test
        swim_file = await self.run_swim_test(num_nodes, duration)
        
        # Generate comparison
        print("Generating comparison analysis...")
        comparison_data = run_protocol_comparison(heartbeat_file, swim_file, self.output_dir)
        
        if comparison_data:
            print("Comparison complete! Check the output directory for results.")
            self._print_summary(comparison_data)
        
        return comparison_data
    
    def _print_summary(self, comparison_data):
        """Print a summary of the comparison results"""
        comp_metrics = comparison_data['comparison_metrics']
        
        print("\n" + "="*60)
        print("PROTOCOL COMPARISON SUMMARY")
        print("="*60)
        
        print(f"Message Efficiency:")
        print(f"  • SWIM reduces messages by {comp_metrics['message_efficiency']['swim_reduction_percent']:.1f}%")
        print(f"  • SWIM saves {comp_metrics['network_utilization']['swim_bandwidth_savings_percent']:.1f}% bandwidth")
        
        print(f"\nFailure Detection:")
        print(f"  • SWIM detects failures {comp_metrics['failure_detection']['swim_faster_by_seconds']:.2f}s faster")
        
        print(f"\nAccuracy:")
        hb_data = comparison_data['heartbeat']
        swim_data = comparison_data['swim']
        print(f"  • Heartbeat accuracy: {hb_data['detection_accuracy']*100:.1f}%")
        print(f"  • SWIM accuracy: {swim_data['detection_accuracy']*100:.1f}%")
        
        # Recommendation
        if (comp_metrics['message_efficiency']['swim_reduction_percent'] > 0 and 
            comp_metrics['failure_detection']['swim_faster_by_seconds'] > 0):
            print(f"\n✅ RECOMMENDATION: SWIM protocol shows better performance")
        else:
            print(f"\n⚠️  RECOMMENDATION: Results vary - consider specific requirements")
        
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Protocol Test Runner")
    parser.add_argument("command", choices=["heartbeat", "swim", "compare", "config"], 
                       help="Test command to run")
    parser.add_argument("--nodes", type=int, default=5, 
                       help="Number of nodes to test with (default: 5)")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Test duration in seconds (default: 60)")
    parser.add_argument("--output-dir", type=str, default="./output", 
                       help="Output directory for results")
    parser.add_argument("--protocol", type=str, choices=["heartbeat", "swim"],
                       help="Switch to specified protocol")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    runner = ProtocolTestRunner(output_dir)
    
    if args.command == "config":
        if args.protocol:
            success = switch_protocol(args.protocol)
            if success:
                print(f"Switched to {args.protocol} protocol")
            else:
                print(f"Failed to switch to {args.protocol} protocol")
        else:
            config = runner.config_manager.get_all_config()
            print("Current Configuration:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        return
    
    # Run async tests
    if args.command == "heartbeat":
        asyncio.run(runner.run_heartbeat_test(args.nodes, args.duration))
    elif args.command == "swim":
        asyncio.run(runner.run_swim_test(args.nodes, args.duration))
    elif args.command == "compare":
        asyncio.run(runner.run_comparison_test(args.nodes, args.duration))

if __name__ == "__main__":
    main() 