import time
import json
import asyncio
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import threading
from collections import defaultdict, deque
import statistics

@dataclass
class NetworkMetrics:
    """Comprehensive network metrics for protocol comparison"""
    timestamp: float
    protocol_type: str  # "heartbeat" or "swim"
    node_id: int
    
    # Message metrics
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    
    # Failure detection metrics
    false_positives: int = 0  # Incorrectly detected failures
    false_negatives: int = 0  # Missed actual failures
    detection_time: float = 0.0  # Time to detect actual failure
    
    # Network congestion metrics
    message_queue_size: int = 0
    message_latency: float = 0.0  # Average message latency
    network_utilization: float = 0.0  # Percentage of bandwidth used
    
    # Protocol-specific metrics
    heartbeat_interval: float = 0.0
    gossip_fanout: int = 0  # For SWIM
    ping_timeout: float = 0.0
    
    # System health metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_connections: int = 0
    
    # Leader election metrics
    leader_changes: int = 0
    election_time: float = 0.0
    split_brain_events: int = 0

class MetricsCollector:
    """Centralized metrics collection and analysis system"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.metrics_history: List[NetworkMetrics] = []
        self.current_metrics: Dict[int, NetworkMetrics] = {}  # node_id -> current metrics
        self.lock = threading.Lock()
        
        # Real-time tracking
        self.message_timestamps: Dict[str, float] = {}  # message_id -> send_timestamp
        self.latency_samples: deque = deque(maxlen=1000)
        self.failure_events: List[Dict] = []
        self.leader_history: List[Dict] = []
        
        # Network simulation state
        self.active_nodes: Set[int] = set()
        self.failed_nodes: Set[int] = set()
        self.network_partitions: List[List[int]] = []
        
    def initialize_node_metrics(self, node_id: int, protocol_type: str):
        """Initialize metrics for a new node"""
        with self.lock:
            self.current_metrics[node_id] = NetworkMetrics(
                timestamp=time.time(),
                protocol_type=protocol_type,
                node_id=node_id
            )
            self.active_nodes.add(node_id)
    
    def record_message_sent(self, node_id: int, message_id: str, message_size: int):
        """Record a message being sent"""
        with self.lock:
            if node_id in self.current_metrics:
                metrics = self.current_metrics[node_id]
                metrics.messages_sent += 1
                metrics.bytes_sent += message_size
                self.message_timestamps[message_id] = time.time()
    
    def record_message_received(self, node_id: int, message_id: str, message_size: int):
        """Record a message being received"""
        with self.lock:
            if node_id in self.current_metrics:
                metrics = self.current_metrics[node_id]
                metrics.messages_received += 1
                metrics.bytes_received += message_size
                
                # Calculate latency if we have send timestamp
                if message_id in self.message_timestamps:
                    latency = time.time() - self.message_timestamps[message_id]
                    self.latency_samples.append(latency)
                    metrics.message_latency = statistics.mean(self.latency_samples)
                    del self.message_timestamps[message_id]
    
    def record_failure_detection(self, detector_id: int, failed_node_id: int, 
                               detection_time: float, is_actual_failure: bool):
        """Record a failure detection event"""
        with self.lock:
            event = {
                'timestamp': time.time(),
                'detector_id': detector_id,
                'failed_node_id': failed_node_id,
                'detection_time': detection_time,
                'is_actual_failure': is_actual_failure,
                'is_false_positive': not is_actual_failure and failed_node_id in self.active_nodes,
                'is_false_negative': is_actual_failure and failed_node_id not in self.failed_nodes
            }
            self.failure_events.append(event)
            
            if detector_id in self.current_metrics:
                metrics = self.current_metrics[detector_id]
                if event['is_false_positive']:
                    metrics.false_positives += 1
                if event['is_false_negative']:
                    metrics.false_negatives += 1
                metrics.detection_time = detection_time
    
    def record_node_failure(self, node_id: int):
        """Record an actual node failure"""
        with self.lock:
            if node_id in self.active_nodes:
                self.active_nodes.remove(node_id)
                self.failed_nodes.add(node_id)
    
    def record_node_recovery(self, node_id: int):
        """Record a node recovery"""
        with self.lock:
            if node_id in self.failed_nodes:
                self.failed_nodes.remove(node_id)
                self.active_nodes.add(node_id)
    
    def record_leader_change(self, old_leader_id: Optional[int], new_leader_id: int, 
                           election_time: float):
        """Record a leader change event"""
        with self.lock:
            event = {
                'timestamp': time.time(),
                'old_leader_id': old_leader_id,
                'new_leader_id': new_leader_id,
                'election_time': election_time
            }
            self.leader_history.append(event)
            
            # Update metrics for all nodes
            for metrics in self.current_metrics.values():
                metrics.leader_changes += 1
                metrics.election_time = election_time
    
    def update_system_metrics(self, node_id: int, cpu_usage: float, memory_usage: float,
                            queue_size: int, active_connections: int):
        """Update system-level metrics"""
        with self.lock:
            if node_id in self.current_metrics:
                metrics = self.current_metrics[node_id]
                metrics.cpu_usage = cpu_usage
                metrics.memory_usage = memory_usage
                metrics.message_queue_size = queue_size
                metrics.active_connections = active_connections
    
    def update_protocol_specific_metrics(self, node_id: int, **kwargs):
        """Update protocol-specific metrics"""
        with self.lock:
            if node_id in self.current_metrics:
                metrics = self.current_metrics[node_id]
                for key, value in kwargs.items():
                    if hasattr(metrics, key):
                        setattr(metrics, key, value)
    
    def snapshot_metrics(self):
        """Take a snapshot of current metrics"""
        with self.lock:
            timestamp = time.time()
            for node_id, metrics in self.current_metrics.items():
                # Create a copy with current timestamp
                snapshot = NetworkMetrics(
                    timestamp=timestamp,
                    protocol_type=metrics.protocol_type,
                    node_id=node_id,
                    messages_sent=metrics.messages_sent,
                    messages_received=metrics.messages_received,
                    bytes_sent=metrics.bytes_sent,
                    bytes_received=metrics.bytes_received,
                    false_positives=metrics.false_positives,
                    false_negatives=metrics.false_negatives,
                    detection_time=metrics.detection_time,
                    message_queue_size=metrics.message_queue_size,
                    message_latency=metrics.message_latency,
                    network_utilization=metrics.network_utilization,
                    heartbeat_interval=metrics.heartbeat_interval,
                    gossip_fanout=metrics.gossip_fanout,
                    ping_timeout=metrics.ping_timeout,
                    cpu_usage=metrics.cpu_usage,
                    memory_usage=metrics.memory_usage,
                    active_connections=metrics.active_connections,
                    leader_changes=metrics.leader_changes,
                    election_time=metrics.election_time,
                    split_brain_events=metrics.split_brain_events
                )
                self.metrics_history.append(snapshot)
    
    def export_metrics(self, filename: str):
        """Export metrics to JSON file"""
        with self.lock:
            data = {
                'metrics_history': [asdict(m) for m in self.metrics_history],
                'failure_events': self.failure_events,
                'leader_history': self.leader_history,
                'summary': self.get_summary_statistics()
            }
            
            filepath = self.output_dir / filename
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics across all metrics"""
        if not self.metrics_history:
            return {}
        
        # Group by protocol type
        heartbeat_metrics = [m for m in self.metrics_history if m.protocol_type == "heartbeat"]
        swim_metrics = [m for m in self.metrics_history if m.protocol_type == "swim"]
        
        def calc_stats(metrics_list):
            if not metrics_list:
                return {}
            
            return {
                'total_messages_sent': sum(m.messages_sent for m in metrics_list),
                'total_messages_received': sum(m.messages_received for m in metrics_list),
                'total_bytes_sent': sum(m.bytes_sent for m in metrics_list),
                'total_bytes_received': sum(m.bytes_received for m in metrics_list),
                'avg_message_latency': statistics.mean([m.message_latency for m in metrics_list if m.message_latency > 0]) if any(m.message_latency > 0 for m in metrics_list) else 0,
                'total_false_positives': sum(m.false_positives for m in metrics_list),
                'total_false_negatives': sum(m.false_negatives for m in metrics_list),
                'avg_detection_time': statistics.mean([m.detection_time for m in metrics_list if m.detection_time > 0]) if any(m.detection_time > 0 for m in metrics_list) else 0,
                'avg_cpu_usage': statistics.mean([m.cpu_usage for m in metrics_list if m.cpu_usage > 0]) if any(m.cpu_usage > 0 for m in metrics_list) else 0,
                'avg_memory_usage': statistics.mean([m.memory_usage for m in metrics_list if m.memory_usage > 0]) if any(m.memory_usage > 0 for m in metrics_list) else 0,
                'total_leader_changes': sum(m.leader_changes for m in metrics_list),
                'avg_election_time': statistics.mean([m.election_time for m in metrics_list if m.election_time > 0]) if any(m.election_time > 0 for m in metrics_list) else 0
            }
        
        return {
            'heartbeat': calc_stats(heartbeat_metrics),
            'swim': calc_stats(swim_metrics),
            'total_nodes': len(self.current_metrics),
            'active_nodes': len(self.active_nodes),
            'failed_nodes': len(self.failed_nodes),
            'collection_duration': time.time() - min(m.timestamp for m in self.metrics_history) if self.metrics_history else 0
        }

# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        from pathlib import Path
        output_dir = Path(__file__).parent / "output"
        _metrics_collector = MetricsCollector(output_dir)
    return _metrics_collector

def initialize_metrics_collection(output_dir: Path):
    """Initialize the global metrics collector"""
    global _metrics_collector
    _metrics_collector = MetricsCollector(output_dir)
    return _metrics_collector 