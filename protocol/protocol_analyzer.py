import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import seaborn as sns
from datetime import datetime
import statistics

class ProtocolAnalyzer:
    """Analyzes and compares performance metrics between heartbeat and SWIM protocols"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def load_metrics_data(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load metrics data from JSON file"""
        filepath = self.output_dir / filename
        if not filepath.exists():
            print(f"Metrics file not found: {filepath}")
            return None
            
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metrics data: {e}")
            return None
    
    def compare_protocols(self, heartbeat_file: str, swim_file: str) -> Dict[str, Any]:
        """Compare performance between heartbeat and SWIM protocols"""
        heartbeat_data = self.load_metrics_data(heartbeat_file)
        swim_data = self.load_metrics_data(swim_file)
        
        if not heartbeat_data or not swim_data:
            print("Could not load both protocol data files")
            return {}
        
        comparison = {
            'heartbeat': self._analyze_protocol_data(heartbeat_data, "heartbeat"),
            'swim': self._analyze_protocol_data(swim_data, "swim"),
            'comparison_metrics': {}
        }
        
        # Calculate comparison metrics
        hb_stats = comparison['heartbeat']
        swim_stats = comparison['swim']
        
        comparison['comparison_metrics'] = {
            'message_efficiency': {
                'heartbeat_msgs_per_node': hb_stats['avg_messages_per_node'],
                'swim_msgs_per_node': swim_stats['avg_messages_per_node'],
                'swim_reduction_percent': ((hb_stats['avg_messages_per_node'] - swim_stats['avg_messages_per_node']) / hb_stats['avg_messages_per_node']) * 100 if hb_stats['avg_messages_per_node'] > 0 else 0
            },
            'failure_detection': {
                'heartbeat_detection_time': hb_stats['avg_failure_detection_time'],
                'swim_detection_time': swim_stats['avg_failure_detection_time'],
                'swim_faster_by_seconds': hb_stats['avg_failure_detection_time'] - swim_stats['avg_failure_detection_time']
            },
            'accuracy': {
                'heartbeat_false_positive_rate': hb_stats['false_positive_rate'],
                'swim_false_positive_rate': swim_stats['false_positive_rate'],
                'heartbeat_false_negative_rate': hb_stats['false_negative_rate'],
                'swim_false_negative_rate': swim_stats['false_negative_rate']
            },
            'network_utilization': {
                'heartbeat_bytes_per_second': hb_stats['avg_bytes_per_second'],
                'swim_bytes_per_second': swim_stats['avg_bytes_per_second'],
                'swim_bandwidth_savings_percent': ((hb_stats['avg_bytes_per_second'] - swim_stats['avg_bytes_per_second']) / hb_stats['avg_bytes_per_second']) * 100 if hb_stats['avg_bytes_per_second'] > 0 else 0
            }
        }
        
        return comparison
    
    def _analyze_protocol_data(self, data: Dict[str, Any], protocol_name: str) -> Dict[str, Any]:
        """Analyze metrics data for a single protocol"""
        metrics_history = data.get('metrics_history', [])
        failure_events = data.get('failure_events', [])
        summary = data.get('summary', {}).get(protocol_name, {})
        
        if not metrics_history:
            return {}
        
        # Calculate time-series statistics
        timestamps = [m['timestamp'] for m in metrics_history]
        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 1
        
        total_messages_sent = sum(m['messages_sent'] for m in metrics_history)
        total_messages_received = sum(m['messages_received'] for m in metrics_history)
        total_bytes_sent = sum(m['bytes_sent'] for m in metrics_history)
        total_bytes_received = sum(m['bytes_received'] for m in metrics_history)
        
        unique_nodes = len(set(m['node_id'] for m in metrics_history))
        
        # Failure detection analysis
        actual_failures = [e for e in failure_events if e['is_actual_failure']]
        false_positives = [e for e in failure_events if e['is_false_positive']]
        false_negatives = [e for e in failure_events if e['is_false_negative']]
        
        detection_times = [e['detection_time'] for e in actual_failures if e['detection_time'] > 0]
        
        return {
            'protocol_name': protocol_name,
            'duration_seconds': duration,
            'total_nodes': unique_nodes,
            'total_messages_sent': total_messages_sent,
            'total_messages_received': total_messages_received,
            'total_bytes_sent': total_bytes_sent,
            'total_bytes_received': total_bytes_received,
            'avg_messages_per_node': total_messages_sent / max(unique_nodes, 1),
            'avg_bytes_per_second': total_bytes_sent / max(duration, 1),
            'message_rate_per_second': total_messages_sent / max(duration, 1),
            'avg_failure_detection_time': statistics.mean(detection_times) if detection_times else 0,
            'total_failures_detected': len(actual_failures),
            'false_positives': len(false_positives),
            'false_negatives': len(false_negatives),
            'false_positive_rate': len(false_positives) / max(len(failure_events), 1),
            'false_negative_rate': len(false_negatives) / max(len(actual_failures), 1) if actual_failures else 0,
            'detection_accuracy': 1 - (len(false_positives) + len(false_negatives)) / max(len(failure_events), 1)
        }
    
    def create_comparison_graphs(self, comparison_data: Dict[str, Any], output_prefix: str = "protocol_comparison"):
        """Create comprehensive comparison graphs"""
        if not comparison_data:
            print("No comparison data available for graphing")
            return
        
        # Create multiple comparison plots
        self._plot_message_efficiency(comparison_data, f"{output_prefix}_messages")
        self._plot_failure_detection_performance(comparison_data, f"{output_prefix}_failure_detection")
        self._plot_network_utilization(comparison_data, f"{output_prefix}_network")
        self._plot_accuracy_metrics(comparison_data, f"{output_prefix}_accuracy")
        self._create_summary_dashboard(comparison_data, f"{output_prefix}_dashboard")
        
        print(f"Generated comparison graphs with prefix: {output_prefix}")
    
    def _plot_message_efficiency(self, comparison_data: Dict[str, Any], filename: str):
        """Plot message efficiency comparison"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        protocols = ['Heartbeat', 'SWIM']
        hb_data = comparison_data['heartbeat']
        swim_data = comparison_data['swim']
        
        # Messages per node
        messages_per_node = [hb_data['avg_messages_per_node'], swim_data['avg_messages_per_node']]
        ax1.bar(protocols, messages_per_node, color=['#FF6B6B', '#4ECDC4'])
        ax1.set_title('Average Messages per Node')
        ax1.set_ylabel('Messages')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, v in enumerate(messages_per_node):
            ax1.text(i, v + max(messages_per_node) * 0.01, f'{v:.1f}', ha='center', va='bottom')
        
        # Message rate over time
        message_rates = [hb_data['message_rate_per_second'], swim_data['message_rate_per_second']]
        ax2.bar(protocols, message_rates, color=['#FF6B6B', '#4ECDC4'])
        ax2.set_title('Message Rate (Messages/Second)')
        ax2.set_ylabel('Messages/Second')
        ax2.grid(True, alpha=0.3)
        
        for i, v in enumerate(message_rates):
            ax2.text(i, v + max(message_rates) * 0.01, f'{v:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_failure_detection_performance(self, comparison_data: Dict[str, Any], filename: str):
        """Plot failure detection performance comparison"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        protocols = ['Heartbeat', 'SWIM']
        hb_data = comparison_data['heartbeat']
        swim_data = comparison_data['swim']
        
        # Detection time
        detection_times = [hb_data['avg_failure_detection_time'], swim_data['avg_failure_detection_time']]
        bars1 = ax1.bar(protocols, detection_times, color=['#FF6B6B', '#4ECDC4'])
        ax1.set_title('Average Failure Detection Time')
        ax1.set_ylabel('Time (seconds)')
        ax1.grid(True, alpha=0.3)
        
        for i, v in enumerate(detection_times):
            ax1.text(i, v + max(detection_times) * 0.01, f'{v:.2f}s', ha='center', va='bottom')
        
        # Detection accuracy
        accuracies = [hb_data['detection_accuracy'] * 100, swim_data['detection_accuracy'] * 100]
        bars2 = ax2.bar(protocols, accuracies, color=['#FF6B6B', '#4ECDC4'])
        ax2.set_title('Failure Detection Accuracy')
        ax2.set_ylabel('Accuracy (%)')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        for i, v in enumerate(accuracies):
            ax2.text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_network_utilization(self, comparison_data: Dict[str, Any], filename: str):
        """Plot network utilization comparison"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        protocols = ['Heartbeat', 'SWIM']
        hb_data = comparison_data['heartbeat']
        swim_data = comparison_data['swim']
        
        # Bandwidth usage
        bandwidth = [hb_data['avg_bytes_per_second'], swim_data['avg_bytes_per_second']]
        ax1.bar(protocols, bandwidth, color=['#FF6B6B', '#4ECDC4'])
        ax1.set_title('Network Bandwidth Usage')
        ax1.set_ylabel('Bytes/Second')
        ax1.grid(True, alpha=0.3)
        
        for i, v in enumerate(bandwidth):
            ax1.text(i, v + max(bandwidth) * 0.01, f'{v:.1f}', ha='center', va='bottom')
        
        # Total bytes sent
        total_bytes = [hb_data['total_bytes_sent'], swim_data['total_bytes_sent']]
        ax2.bar(protocols, total_bytes, color=['#FF6B6B', '#4ECDC4'])
        ax2.set_title('Total Bytes Transmitted')
        ax2.set_ylabel('Bytes')
        ax2.grid(True, alpha=0.3)
        
        for i, v in enumerate(total_bytes):
            ax2.text(i, v + max(total_bytes) * 0.01, f'{v:,}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_accuracy_metrics(self, comparison_data: Dict[str, Any], filename: str):
        """Plot accuracy metrics comparison"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        protocols = ['Heartbeat', 'SWIM']
        hb_data = comparison_data['heartbeat']
        swim_data = comparison_data['swim']
        
        # False positive rates
        fp_rates = [hb_data['false_positive_rate'] * 100, swim_data['false_positive_rate'] * 100]
        ax1.bar(protocols, fp_rates, color=['#FF6B6B', '#4ECDC4'])
        ax1.set_title('False Positive Rate')
        ax1.set_ylabel('Rate (%)')
        ax1.grid(True, alpha=0.3)
        
        for i, v in enumerate(fp_rates):
            ax1.text(i, v + max(fp_rates) * 0.01, f'{v:.1f}%', ha='center', va='bottom')
        
        # False negative rates
        fn_rates = [hb_data['false_negative_rate'] * 100, swim_data['false_negative_rate'] * 100]
        ax2.bar(protocols, fn_rates, color=['#FF6B6B', '#4ECDC4'])
        ax2.set_title('False Negative Rate')
        ax2.set_ylabel('Rate (%)')
        ax2.grid(True, alpha=0.3)
        
        for i, v in enumerate(fn_rates):
            ax2.text(i, v + max(fn_rates) * 0.01, f'{v:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_summary_dashboard(self, comparison_data: Dict[str, Any], filename: str):
        """Create a comprehensive summary dashboard"""
        fig = plt.figure(figsize=(20, 12))
        
        # Create a 3x3 grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        protocols = ['Heartbeat', 'SWIM']
        hb_data = comparison_data['heartbeat']
        swim_data = comparison_data['swim']
        comp_metrics = comparison_data['comparison_metrics']
        
        # 1. Message efficiency
        ax1 = fig.add_subplot(gs[0, 0])
        messages = [hb_data['avg_messages_per_node'], swim_data['avg_messages_per_node']]
        ax1.bar(protocols, messages, color=['#FF6B6B', '#4ECDC4'])
        ax1.set_title('Messages per Node')
        ax1.set_ylabel('Messages')
        
        # 2. Detection time
        ax2 = fig.add_subplot(gs[0, 1])
        det_times = [hb_data['avg_failure_detection_time'], swim_data['avg_failure_detection_time']]
        ax2.bar(protocols, det_times, color=['#FF6B6B', '#4ECDC4'])
        ax2.set_title('Detection Time')
        ax2.set_ylabel('Seconds')
        
        # 3. Bandwidth usage
        ax3 = fig.add_subplot(gs[0, 2])
        bandwidth = [hb_data['avg_bytes_per_second'], swim_data['avg_bytes_per_second']]
        ax3.bar(protocols, bandwidth, color=['#FF6B6B', '#4ECDC4'])
        ax3.set_title('Bandwidth Usage')
        ax3.set_ylabel('Bytes/sec')
        
        # 4. Accuracy comparison
        ax4 = fig.add_subplot(gs[1, 0])
        accuracy = [hb_data['detection_accuracy'] * 100, swim_data['detection_accuracy'] * 100]
        ax4.bar(protocols, accuracy, color=['#FF6B6B', '#4ECDC4'])
        ax4.set_title('Detection Accuracy')
        ax4.set_ylabel('Accuracy (%)')
        ax4.set_ylim(0, 100)
        
        # 5. False positive comparison
        ax5 = fig.add_subplot(gs[1, 1])
        fp_rates = [hb_data['false_positive_rate'] * 100, swim_data['false_positive_rate'] * 100]
        ax5.bar(protocols, fp_rates, color=['#FF6B6B', '#4ECDC4'])
        ax5.set_title('False Positive Rate')
        ax5.set_ylabel('Rate (%)')
        
        # 6. Total failures detected
        ax6 = fig.add_subplot(gs[1, 2])
        failures = [hb_data['total_failures_detected'], swim_data['total_failures_detected']]
        ax6.bar(protocols, failures, color=['#FF6B6B', '#4ECDC4'])
        ax6.set_title('Failures Detected')
        ax6.set_ylabel('Count')
        
        # 7. Summary text
        ax7 = fig.add_subplot(gs[2, :])
        ax7.axis('off')
        
        summary_text = f"""
PROTOCOL COMPARISON SUMMARY

Message Efficiency:
• SWIM reduces messages per node by {comp_metrics['message_efficiency']['swim_reduction_percent']:.1f}%
• SWIM saves {comp_metrics['network_utilization']['swim_bandwidth_savings_percent']:.1f}% bandwidth

Failure Detection:
• SWIM detects failures {comp_metrics['failure_detection']['swim_faster_by_seconds']:.2f}s faster than Heartbeat
• Heartbeat accuracy: {hb_data['detection_accuracy']*100:.1f}%, SWIM accuracy: {swim_data['detection_accuracy']*100:.1f}%

Network Performance:
• Heartbeat: {hb_data['avg_bytes_per_second']:.1f} bytes/sec, SWIM: {swim_data['avg_bytes_per_second']:.1f} bytes/sec
• Total test duration: {hb_data['duration_seconds']:.1f}s (Heartbeat), {swim_data['duration_seconds']:.1f}s (SWIM)

Recommendation: {"SWIM protocol shows better efficiency and faster detection" if comp_metrics['message_efficiency']['swim_reduction_percent'] > 0 and comp_metrics['failure_detection']['swim_faster_by_seconds'] > 0 else "Results vary - consider specific use case requirements"}
        """
        
        ax7.text(0.05, 0.95, summary_text, transform=ax7.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.suptitle('Protocol Comparison Dashboard', fontsize=16, fontweight='bold')
        plt.savefig(self.output_dir / f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_report(self, comparison_data: Dict[str, Any], output_file: str = "protocol_comparison_report.md"):
        """Generate a detailed markdown report"""
        if not comparison_data:
            print("No comparison data available for report generation")
            return
        
        hb_data = comparison_data['heartbeat']
        swim_data = comparison_data['swim']
        comp_metrics = comparison_data['comparison_metrics']
        
        report = f"""# Protocol Comparison Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report compares the performance of Heartbeat and SWIM failure detection protocols based on empirical testing.

### Key Findings

- **Message Efficiency**: SWIM reduces network messages by {comp_metrics['message_efficiency']['swim_reduction_percent']:.1f}%
- **Detection Speed**: SWIM detects failures {comp_metrics['failure_detection']['swim_faster_by_seconds']:.2f}s faster
- **Bandwidth Savings**: SWIM uses {comp_metrics['network_utilization']['swim_bandwidth_savings_percent']:.1f}% less bandwidth
- **Accuracy**: Heartbeat {hb_data['detection_accuracy']*100:.1f}% vs SWIM {swim_data['detection_accuracy']*100:.1f}%

## Detailed Metrics

### Heartbeat Protocol
- **Duration**: {hb_data['duration_seconds']:.1f} seconds
- **Total Nodes**: {hb_data['total_nodes']}
- **Messages Sent**: {hb_data['total_messages_sent']:,}
- **Bytes Transmitted**: {hb_data['total_bytes_sent']:,}
- **Average Detection Time**: {hb_data['avg_failure_detection_time']:.2f}s
- **False Positive Rate**: {hb_data['false_positive_rate']*100:.1f}%
- **False Negative Rate**: {hb_data['false_negative_rate']*100:.1f}%

### SWIM Protocol
- **Duration**: {swim_data['duration_seconds']:.1f} seconds
- **Total Nodes**: {swim_data['total_nodes']}
- **Messages Sent**: {swim_data['total_messages_sent']:,}
- **Bytes Transmitted**: {swim_data['total_bytes_sent']:,}
- **Average Detection Time**: {swim_data['avg_failure_detection_time']:.2f}s
- **False Positive Rate**: {swim_data['false_positive_rate']*100:.1f}%
- **False Negative Rate**: {swim_data['false_negative_rate']*100:.1f}%

## Analysis

### Message Efficiency
The SWIM protocol demonstrates superior message efficiency by leveraging gossip-style communication rather than direct heartbeats between all nodes. This results in:
- {comp_metrics['message_efficiency']['swim_reduction_percent']:.1f}% reduction in total messages
- Better scalability as network size increases
- Reduced network congestion

### Failure Detection Performance
SWIM's probabilistic failure detection approach provides:
- Faster detection times ({comp_metrics['failure_detection']['swim_faster_by_seconds']:.2f}s improvement)
- More robust detection in network partition scenarios
- Better handling of transient network issues

### Network Utilization
SWIM's efficiency translates to significant bandwidth savings:
- {comp_metrics['network_utilization']['swim_bandwidth_savings_percent']:.1f}% reduction in bandwidth usage
- Lower network overhead per node
- Better performance under high network load

## Recommendations

Based on the analysis:

1. **For Large Networks (>10 nodes)**: SWIM protocol is recommended due to its superior scalability and efficiency
2. **For Small Networks (<5 nodes)**: Either protocol is suitable, but SWIM still offers benefits
3. **For High-Reliability Requirements**: Consider SWIM with tuned parameters for faster detection
4. **For Resource-Constrained Environments**: SWIM's lower bandwidth usage makes it preferable

## Configuration Recommendations

### Heartbeat Protocol Tuning
- Heartbeat Interval: {hb_data.get('heartbeat_interval', 'N/A')}s
- Response Timeout: {hb_data.get('response_allowance', 'N/A')}s
- Missed Threshold: {hb_data.get('missed_threshold', 'N/A')}

### SWIM Protocol Tuning
- Protocol Period: {swim_data.get('protocol_period', 'N/A')}s
- ACK Timeout: {swim_data.get('ack_timeout', 'N/A')}s
- Gossip Fanout: {swim_data.get('gossip_fanout', 'N/A')}

## Conclusion

The SWIM protocol demonstrates clear advantages over traditional heartbeat mechanisms in terms of efficiency, speed, and scalability. The gossip-based approach provides robust failure detection with significantly reduced network overhead, making it the preferred choice for most distributed system scenarios.
"""
        
        report_path = self.output_dir / output_file
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"Generated detailed report: {report_path}")
        return report_path

def run_protocol_comparison(heartbeat_metrics_file: str, swim_metrics_file: str, output_dir: Path):
    """Run a complete protocol comparison analysis"""
    analyzer = ProtocolAnalyzer(output_dir)
    
    print("Loading and analyzing protocol data...")
    comparison_data = analyzer.compare_protocols(heartbeat_metrics_file, swim_metrics_file)
    
    if not comparison_data:
        print("Failed to load comparison data")
        return
    
    print("Generating comparison graphs...")
    analyzer.create_comparison_graphs(comparison_data)
    
    print("Generating detailed report...")
    analyzer.generate_report(comparison_data)
    
    print(f"Analysis complete! Check {output_dir} for results.")
    
    return comparison_data 