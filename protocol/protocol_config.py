import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class ProtocolConfig:
    """Configuration for failure detection protocols"""
    # Protocol selection
    failure_detection_protocol: str = "heartbeat"  # "heartbeat" or "swim"
    
    # Heartbeat protocol parameters
    heartbeat_interval: float = 5.0
    response_allowance: float = 1.0
    missed_threshold: int = 5
    attendance_interval: float = 5.0
    
    # SWIM protocol parameters
    swim_protocol_period: float = 1.0
    swim_ack_timeout: float = 0.5
    swim_suspect_timeout: float = 3.0
    swim_indirect_ping_nodes: int = 3
    swim_gossip_fanout: int = 3
    swim_max_gossip_per_message: int = 5
    
    # Metrics collection
    metrics_enabled: bool = True
    metrics_snapshot_interval: float = 5.0
    metrics_export_interval: float = 60.0
    
    # Network simulation parameters
    network_latency_ms: float = 10.0
    packet_loss_rate: float = 0.0
    network_partition_probability: float = 0.0

class ProtocolConfigManager:
    """Manages protocol configuration with runtime switching capabilities"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path(__file__).parent / "protocol_config.json"
        self.config = ProtocolConfig()
        self.load_config()
        
    def load_config(self) -> ProtocolConfig:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    # Update config with loaded values
                    for key, value in config_data.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
                print(f"Loaded protocol configuration from {self.config_file}")
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        else:
            # Create default config file
            self.save_config()
        return self.config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            print(f"Saved protocol configuration to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def switch_protocol(self, protocol: str) -> bool:
        """Switch to a different failure detection protocol"""
        if protocol not in ["heartbeat", "swim"]:
            print(f"Invalid protocol: {protocol}. Must be 'heartbeat' or 'swim'")
            return False
        
        old_protocol = self.config.failure_detection_protocol
        self.config.failure_detection_protocol = protocol
        self.save_config()
        
        print(f"Switched protocol from {old_protocol} to {protocol}")
        print("Note: Restart devices for changes to take effect")
        return True
    
    def update_heartbeat_config(self, **kwargs):
        """Update heartbeat protocol parameters"""
        valid_params = {
            'heartbeat_interval', 'response_allowance', 'missed_threshold', 'attendance_interval'
        }
        
        for key, value in kwargs.items():
            if key in valid_params and hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"Updated {key} to {value}")
            else:
                print(f"Invalid heartbeat parameter: {key}")
        
        self.save_config()
    
    def update_swim_config(self, **kwargs):
        """Update SWIM protocol parameters"""
        valid_params = {
            'swim_protocol_period', 'swim_ack_timeout', 'swim_suspect_timeout',
            'swim_indirect_ping_nodes', 'swim_gossip_fanout', 'swim_max_gossip_per_message'
        }
        
        for key, value in kwargs.items():
            if key in valid_params and hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"Updated {key} to {value}")
            else:
                print(f"Invalid SWIM parameter: {key}")
        
        self.save_config()
    
    def update_metrics_config(self, **kwargs):
        """Update metrics collection parameters"""
        valid_params = {
            'metrics_enabled', 'metrics_snapshot_interval', 'metrics_export_interval'
        }
        
        for key, value in kwargs.items():
            if key in valid_params and hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"Updated {key} to {value}")
            else:
                print(f"Invalid metrics parameter: {key}")
        
        self.save_config()
    
    def get_current_protocol(self) -> str:
        """Get currently configured protocol"""
        return self.config.failure_detection_protocol
    
    def get_protocol_params(self, protocol: str) -> Dict[str, Any]:
        """Get parameters for a specific protocol"""
        if protocol == "heartbeat":
            return {
                'heartbeat_interval': self.config.heartbeat_interval,
                'response_allowance': self.config.response_allowance,
                'missed_threshold': self.config.missed_threshold,
                'attendance_interval': self.config.attendance_interval
            }
        elif protocol == "swim":
            return {
                'protocol_period': self.config.swim_protocol_period,
                'ack_timeout': self.config.swim_ack_timeout,
                'suspect_timeout': self.config.swim_suspect_timeout,
                'indirect_ping_nodes': self.config.swim_indirect_ping_nodes,
                'gossip_fanout': self.config.swim_gossip_fanout,
                'max_gossip_per_message': self.config.swim_max_gossip_per_message
            }
        else:
            return {}
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration parameters"""
        return asdict(self.config)
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = ProtocolConfig()
        self.save_config()
        print("Reset configuration to defaults")

# Global configuration manager instance
_config_manager: Optional[ProtocolConfigManager] = None

def get_config_manager() -> ProtocolConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ProtocolConfigManager()
    return _config_manager

def get_current_protocol() -> str:
    """Get the currently configured protocol"""
    return get_config_manager().get_current_protocol()

def switch_protocol(protocol: str) -> bool:
    """Switch to a different protocol"""
    return get_config_manager().switch_protocol(protocol) 