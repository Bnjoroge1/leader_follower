# Hierarchical Leader-Follower Protocol

This document describes the hierarchical neighborhood extension to the leader-follower protocol, designed to improve scalability from O(N²) to O(N×k) message complexity.

## Overview

The hierarchical extension organizes devices into neighborhoods with local leaders, coordinated by a council of leaders and a super-leader. This maintains the existing protocol semantics while dramatically reducing message overhead for large deployments.

### Key Benefits

- **Scalable Message Complexity**: O(N×k) instead of O(N²) where k = neighborhood size
- **Distributed Leadership**: Multiple neighborhood leaders instead of single global leader
- **Localized Failure Detection**: SWIM/heartbeat runs within neighborhoods
- **Fault Tolerance**: Multiple levels of redundancy and no single point of failure
- **Backward Compatibility**: Can be enabled/disabled via configuration

## Architecture

### Two-Level Hierarchy
1. **Neighborhoods**: Groups of 10-40 devices with one neighborhood leader
2. **Council**: All neighborhood leaders form a council with one super-leader

### Roles
- **Device**: Regular follower within a neighborhood
- **Neighborhood Leader**: Manages local neighborhood, participates in council
- **Super Leader**: Coordinates the council and handles global decisions

## Quick Start

### 1. Enable Hierarchical Mode

```bash
# Enable hierarchy with default settings
python3 hierarchy_test_runner.py enable

# Or configure manually
python3 -c "
from protocol_config import get_config_manager
config = get_config_manager()
config.enable_hierarchy(True)
config.update_hierarchy_config(
    target_neighborhood_size=25,
    max_neighborhood_size=40,
    min_neighborhood_size=10
)
"
```

### 2. Run a Test

```bash
# Basic functionality test
python3 hierarchy_test_runner.py test --devices 20 --duration 60

# Compare with flat protocol
python3 hierarchy_test_runner.py compare --devices 50

# View current configuration
python3 hierarchy_test_runner.py config
```

### 3. Run the Demo

```bash
# See how the hierarchy works conceptually
python3 hierarchy_demo.py
```

## Configuration Options

### Core Settings
```python
hierarchy_enabled: bool = False              # Enable/disable hierarchy
neighborhood_strategy: str = "hash"          # "hash", "geographic", "manual"
target_neighborhood_size: int = 25           # Optimal neighborhood size
max_neighborhood_size: int = 40              # Split threshold
min_neighborhood_size: int = 10              # Merge threshold
```

### Timing Parameters
```python
council_heartbeat_interval: float = 10.0     # Council member heartbeats
cross_neighborhood_timeout: float = 5.0      # Cross-neighborhood operation timeout
rebalance_cooldown: float = 60.0             # Minimum time between rebalancing
summary_report_interval: float = 30.0        # Neighborhood summary reports
```

## How It Works

### Device Startup
1. **Neighborhood Assignment**: Device computes `neighborhood_id = hash(device_id) % num_neighborhoods`
2. **Discovery**: Listens for neighborhood leader attendance messages
3. **Join Request**: Sends `NEIGHBORHOOD_JOIN_REQUEST` to leader
4. **Integration**: Added to local device list and SWIM membership

### Leadership Election
1. **Neighborhood Election**: Devices in same neighborhood elect local leader (lowest ID wins)
2. **Council Formation**: Neighborhood leaders form council
3. **Super Leader Election**: Council elects super leader (lowest ID among leaders)

### Message Flow

#### Local Operations (within neighborhood)
- **Attendance**: Leader → neighborhood devices (every 5s)
- **Check-ins**: Leader ↔ individual devices
- **SWIM**: Failure detection within neighborhood
- **Device List**: Leader broadcasts to neighborhood

#### Council Operations (between leaders)
- **Summaries**: Neighborhood leaders → super leader (every 30s)
- **Heartbeats**: Leaders → super leader (every 10s)
- **Announcements**: Super leader → all leaders

#### Cross-Neighborhood (rare)
- **Routing**: Device A → Leader A → Super Leader → Leader B → Device B
- **Global Broadcasts**: Super leader → all leaders → all devices

### Failure Handling

#### Device Failure
1. Detected by neighborhood leader via SWIM/heartbeat
2. Removed from local device list
3. Summary sent to super leader

#### Neighborhood Leader Failure
1. Detected by local devices via timeout
2. Local election among remaining devices
3. New leader joins council
4. Super leader updates council membership

#### Super Leader Failure
1. Detected by council members via timeout
2. Council election among remaining leaders
3. New super leader announces to all leaders

## Message Types

### Neighborhood Coordination
- `NEIGHBORHOOD_JOIN_REQUEST`: Device requests to join neighborhood
- `NEIGHBORHOOD_JOIN_ACCEPT`: Leader accepts join request
- `NEIGHBORHOOD_LEAVE`: Device leaves neighborhood

### Council Operations
- `COUNCIL_JOIN`: New leader joins council
- `COUNCIL_SUMMARY`: Periodic neighborhood summary
- `COUNCIL_HEARTBEAT`: Leader heartbeat to super leader
- `SUPER_LEADER_ANNOUNCE`: New super leader announcement

### Routing and Rebalancing
- `CROSS_NEIGHBORHOOD_ROUTE`: Route message between neighborhoods
- `REBALANCE_REQUEST`: Request neighborhood split/merge
- `REBALANCE_ACCEPT`: Accept rebalancing operation

## Performance Characteristics

### Message Complexity
```
Flat Protocol:     O(N²) - every device talks to every device
Hierarchical:      O(N×k + m²) where k=neighborhood size, m=neighborhoods
Optimal (k=√N):    O(N^1.5) vs O(N²) flat
```

### Memory Usage
```
Flat:              O(N) device info per device
Hierarchical:      O(k + m) per device = O(√N) for optimal k
```

### Scalability Results
| Devices | Flat Messages | Hierarchical | Reduction |
|---------|---------------|--------------|-----------|
| 100     | 10,000        | 2,500        | 75%       |
| 1,000   | 1,000,000     | 25,000       | 97.5%     |
| 10,000  | 100,000,000   | 250,000      | 99.75%    |

## Integration with Existing Features

### SWIM Protocol
- Runs locally within neighborhoods (better performance)
- Optional cross-neighborhood SWIM for leader coordination
- Maintains all existing SWIM guarantees within neighborhoods

### Metrics Collection
- Extended to track neighborhood-level metrics
- Council coordination metrics
- Hierarchical vs flat comparison data

### Protocol Switching
- Runtime switching between flat and hierarchical modes
- Backward compatibility with existing device configurations
- Gradual rollout support

## Limitations and Considerations

### Current Limitations
1. **Cross-neighborhood latency**: 4x flat protocol for cross-neighborhood messages
2. **Leader bottlenecks**: Neighborhood leaders handle both local and routing duties
3. **Rebalancing complexity**: Neighborhood splits/merges require coordination
4. **Configuration complexity**: More parameters to tune

### When to Use
- **Optimal for**: 100-10,000 devices with local communication patterns
- **Good for**: Systems where most communication is within neighborhoods
- **Consider alternatives for**: Small systems (<50 devices) or high cross-neighborhood traffic

### Best Practices
1. **Neighborhood Size**: 15-40 devices for optimal balance
2. **Communication Patterns**: Ensure 80%+ traffic is local to neighborhoods
3. **Network Reliability**: Higher leader availability requirements
4. **Monitoring**: Track per-neighborhood and council metrics

## Troubleshooting

### Common Issues

#### High Cross-Neighborhood Latency
```bash
# Check if communication patterns are local
# Consider adjusting neighborhood assignment strategy
python3 hierarchy_test_runner.py config
```

#### Leader Overload
```bash
# Reduce neighborhood size or split overloaded neighborhoods
# Monitor leader CPU/memory usage in metrics
```

#### Split-Brain Scenarios
```bash
# Check council heartbeat intervals
# Ensure network partitions are rare
# Monitor council stability in metrics
```

### Debug Commands
```bash
# View hierarchy configuration
python3 hierarchy_test_runner.py config

# Test with different sizes
python3 hierarchy_test_runner.py test --devices 50 --duration 120

# Compare performance
python3 hierarchy_test_runner.py compare --devices 100

# Disable hierarchy if needed
python3 hierarchy_test_runner.py disable
```

## Future Enhancements

### Phase 2 Features
1. **Cross-neighborhood routing optimization**: Direct connections for high-traffic pairs
2. **Geographic neighborhoods**: Location-aware assignment
3. **Dynamic rebalancing**: Automatic split/merge based on load
4. **Multi-level hierarchy**: 3+ levels for very large deployments

### Advanced Features
1. **Load balancing**: Automatic leader migration
2. **Partition tolerance**: Independent neighborhood operation
3. **Security**: Authenticated council membership
4. **Performance tuning**: Adaptive timeout and sizing

## References

- **SWIM Protocol**: Original failure detection protocol
- **Hierarchical Systems**: Academic research on scalable distributed systems
- **Leader Election**: Distributed consensus algorithms
- **Network Partitioning**: Fault tolerance in distributed systems

---

For questions or issues, check the existing protocol documentation and test runners for examples of hierarchical functionality in action.
