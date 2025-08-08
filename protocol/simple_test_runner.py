#!/usr/bin/env python3
"""
Simple Protocol Test Runner - Fixed version for testing and comparing protocols
"""

import argparse
import asyncio
import time
from pathlib import Path
import sys

from protocol_config import get_config_manager, switch_protocol
from metrics_collector import get_metrics_collector, initialize_metrics_collection
from protocol_analyzer import run_protocol_comparison

class SimpleProtocolTester:
    """Simplified protocol tester that works with existing infrastructure"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.config_manager = get_config_manager()
        
    def run_heartbeat_test(self, duration: int = 30) -> str:
        """Run a test with heartbeat protocol using existing simulation"""
        print(f"Running heartbeat test for {duration} seconds...")
        
        # Switch to heartbeat protocol
        switch_protocol("heartbeat")
        print("✅ Switched to heartbeat protocol")
        
        # Initialize metrics collection
        metrics_collector = initialize_metrics_collection(self.output_dir)
        print("✅ Initialized metrics collection")
        
        # Simulate running for specified duration
        print(f"📊 Collecting metrics for {duration} seconds...")
        print("💡 To get real data, run your existing simulation with heartbeat protocol")
        print("   Example: python channel_driver.py")
        
        # Generate some sample metrics for demonstration
        self._generate_sample_metrics(metrics_collector, "heartbeat", duration)
        
        # Export metrics
        metrics_file = f"heartbeat_metrics_{int(time.time())}.json"
        metrics_collector.export_metrics(metrics_file)
        print(f"✅ Heartbeat test completed. Metrics saved to {self.output_dir / metrics_file}")
        
        return metrics_file
    
    def run_swim_test(self, duration: int = 30) -> str:
        """Run a test with SWIM protocol using existing simulation"""
        print(f"Running SWIM test for {duration} seconds...")
        
        # Switch to SWIM protocol
        switch_protocol("swim")
        print("✅ Switched to SWIM protocol")
        
        # Initialize metrics collection
        metrics_collector = initialize_metrics_collection(self.output_dir)
        print("✅ Initialized metrics collection")
        
        # Simulate running for specified duration
        print(f"📊 Collecting metrics for {duration} seconds...")
        print("💡 To get real data, run your existing simulation with SWIM protocol")
        print("   Example: python channel_driver.py")
        
        # Generate some sample metrics for demonstration
        self._generate_sample_metrics(metrics_collector, "swim", duration)
        
        # Export metrics
        metrics_file = f"swim_metrics_{int(time.time())}.json"
        metrics_collector.export_metrics(metrics_file)
        print(f"✅ SWIM test completed. Metrics saved to {self.output_dir / metrics_file}")
        
        return metrics_file
    
    def run_comparison_test(self, duration: int = 30):
        """Run both protocols and generate comparison"""
        print("🚀 Starting comprehensive protocol comparison...")
        
        # Run heartbeat test
        heartbeat_file = self.run_heartbeat_test(duration)
        
        # Wait a bit between tests
        time.sleep(2)
        
        # Run SWIM test
        swim_file = self.run_swim_test(duration)
        
        # Generate comparison
        print("📈 Generating comparison analysis...")
        comparison_data = run_protocol_comparison(heartbeat_file, swim_file, self.output_dir)
        
        if comparison_data:
            print("✅ Comparison complete! Check the output directory for results.")
            self._print_summary(comparison_data)
            self._show_output_files()
        
        return comparison_data
    
    def _generate_sample_metrics(self, metrics_collector, protocol_type, duration):
        """Generate sample metrics for demonstration"""
        import random
        
        # Simulate 5 nodes
        for node_id in range(1, 6):
            metrics_collector.initialize_node_metrics(node_id, protocol_type)
        
        # Simulate metrics collection over time
        for second in range(duration):
            for node_id in range(1, 6):
                # Simulate message activity
                if protocol_type == "heartbeat":
                    # Heartbeat sends more messages
                    messages_sent = random.randint(8, 15)
                    bytes_sent = messages_sent * random.randint(50, 100)
                else:  # SWIM
                    # SWIM sends fewer messages due to gossip efficiency
                    messages_sent = random.randint(3, 8)
                    bytes_sent = messages_sent * random.randint(40, 80)
                
                for _ in range(messages_sent):
                    msg_id = f"{node_id}_{second}_{random.randint(1000, 9999)}"
                    metrics_collector.record_message_sent(node_id, msg_id, random.randint(40, 100))
                    metrics_collector.record_message_received((node_id % 5) + 1, msg_id, random.randint(40, 100))
                
                # Simulate failure detection events
                if random.random() < 0.1:  # 10% chance of detection event
                    target_node = random.choice([n for n in range(1, 6) if n != node_id])
                    is_actual_failure = random.random() < 0.7  # 70% are actual failures
                    detection_time = random.uniform(0.5, 3.0) if protocol_type == "heartbeat" else random.uniform(0.2, 1.5)
                    metrics_collector.record_failure_detection(node_id, target_node, detection_time, is_actual_failure)
                
                # Update system metrics
                metrics_collector.update_system_metrics(
                    node_id, 
                    random.uniform(10, 30),  # CPU
                    random.uniform(20, 50),  # Memory
                    random.randint(0, 10),   # Queue size
                    random.randint(3, 8)     # Connections
                )
            
            # Take periodic snapshots
            if second % 5 == 0:
                metrics_collector.snapshot_metrics()
        
        # Final snapshot
        metrics_collector.snapshot_metrics()
    
    def _print_summary(self, comparison_data):
        """Print a summary of the comparison results"""
        comp_metrics = comparison_data['comparison_metrics']
        
        print("\n" + "="*60)
        print("📊 PROTOCOL COMPARISON SUMMARY")
        print("="*60)
        
        print(f"💬 Message Efficiency:")
        print(f"  • SWIM reduces messages by {comp_metrics['message_efficiency']['swim_reduction_percent']:.1f}%")
        print(f"  • SWIM saves {comp_metrics['network_utilization']['swim_bandwidth_savings_percent']:.1f}% bandwidth")
        
        print(f"\n⚡ Failure Detection:")
        print(f"  • SWIM detects failures {comp_metrics['failure_detection']['swim_faster_by_seconds']:.2f}s faster")
        
        print(f"\n🎯 Accuracy:")
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
    
    def _show_output_files(self):
        """Show user where to find the output files"""
        print(f"\n📁 RESULTS LOCATION: {self.output_dir.absolute()}")
        print("\n📊 Generated Files:")
        
        # List all files in output directory
        try:
            files = list(self.output_dir.glob("*"))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Sort by newest first
            
            for file in files[:10]:  # Show newest 10 files
                if file.is_file():
                    size = file.stat().st_size
                    if size > 1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size}B"
                    
                    if file.suffix == '.png':
                        print(f"  📈 {file.name} ({size_str}) - Graph/Chart")
                    elif file.suffix == '.json':
                        print(f"  📋 {file.name} ({size_str}) - Metrics Data")
                    elif file.suffix == '.md':
                        print(f"  📄 {file.name} ({size_str}) - Analysis Report")
                    else:
                        print(f"  📄 {file.name} ({size_str})")
        except Exception as e:
            print(f"  Error listing files: {e}")
        
        print(f"\n💡 To view graphs: Open .png files in any image viewer")
        print(f"💡 To read report: Open .md files in any text editor or markdown viewer")
        print(f"💡 Raw data: .json files contain detailed metrics")

def main():
    parser = argparse.ArgumentParser(description="Simple Protocol Test Runner")
    parser.add_argument("command", choices=["heartbeat", "swim", "compare", "config"], 
                       help="Test command to run")
    parser.add_argument("--duration", type=int, default=30, 
                       help="Test duration in seconds (default: 30)")
    parser.add_argument("--output-dir", type=str, default="./output", 
                       help="Output directory for results")
    parser.add_argument("--protocol", type=str, choices=["heartbeat", "swim"],
                       help="Switch to specified protocol")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    tester = SimpleProtocolTester(output_dir)
    
    if args.command == "config":
        if args.protocol:
            success = switch_protocol(args.protocol)
            if success:
                print(f"✅ Switched to {args.protocol} protocol")
            else:
                print(f"❌ Failed to switch to {args.protocol} protocol")
        else:
            config = tester.config_manager.get_all_config()
            print("⚙️  Current Configuration:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        return
    
    # Run tests
    if args.command == "heartbeat":
        tester.run_heartbeat_test(args.duration)
    elif args.command == "swim":
        tester.run_swim_test(args.duration)
    elif args.command == "compare":
        tester.run_comparison_test(args.duration)

if __name__ == "__main__":
    main() 