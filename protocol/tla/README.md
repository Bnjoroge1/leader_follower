

# Leader-Follower Protocol Verification

This directory contains TLA+ specifications for verifying the Leader-Follower protocol's correctness.

## Overview

The specification verifies critical properties of the Leader-Follower protocol:
- Leader election correctness
- Network joining process
- Device state transitions
- Message handling
- Check-in protocol

## Files

- `LeaderFollower.tla` - Main protocol specification
- `LeaderFollower.cfg` - TLC model checker configuration
- `spec2.tla.tl.tla` - Alternative specification (network topology focused)

## Running the Model Checker

1. Install the TLA+ Toolbox from [TLA+ Releases](https://github.com/tlaplus/tlaplus/releases)

2. Open the specification:
   - File → Open Spec → Add New Spec
   - Select `LeaderFollower.tla`

3. Create a new model:
   - File → New Model
   - Name it (e.g., "LeaderFollowerModel")

4. Configure the model:
```
SPECIFICATION Spec

CONSTANTS
    MaxDevices = 2

INVARIANTS
    AtMostOneLeader

PROPERTIES
    EventuallyHaveLeader
    AllDevicesEventuallyJoin
```

5. Run the model checker:
   - Click "Run TLC" in the model overview

## Verified Properties

### Safety Properties
- `AtMostOneLeader`: Only one leader exists at any time
```tla
AtMostOneLeader == 
    Cardinality({d \in devices : status[d] = LEADER}) <= 1
```

### Liveness Properties
- `EventuallyHaveLeader`: A leader will eventually be elected
```tla
EventuallyHaveLeader == 
    <>(leader /= NULL)
```

- `AllDevicesEventuallyJoin`: All devices eventually join the network
```tla
AllDevicesEventuallyJoin == 
    [](Cardinality(devices) > 0 => <>(network = devices))
```

## State Space Statistics

Current verification coverage (as of latest run):
- States generated: 309,107,708
- Distinct states: 23,772,947
- Queue size: 9,123,346

## Common Issues and Solutions

### State Space Explosion
If encountering state space explosion:
1. Reduce `MaxDevices` in configuration
2. Add state constraints:
```tla
CONSTRAINT
    Cardinality(messages) <= 3
```

### Memory Issues
If running out of memory:
1. Increase JVM heap size:
   - Model → Advanced Options
   - Set `-Xmx4096m` in JVM Arguments


## Adding New Properties

To verify additional properties:

1. Add the property to `LeaderFollower.tla`:
```tla
NewProperty ==
    [](property_definition)
```

2. Add to configuration:
```
PROPERTIES
    NewProperty
```

## Debugging Tips

1. Enable detailed error traces:
   - Model → Advanced Options
   - Check "Create detailed error trace"

2. View state space statistics:
   - Click "Statistics" in model overview
   - Monitor coverage and distinct states

3. Use TLC profiler:
   - Model → Advanced Options
   - Enable "Profiling"

## Contributing

When adding new verification properties:

1. Document the property purpose
2. Include expected behavior
3. Add relevant test configurations
4. Update this README with new properties

## References

- [TLA+ Documentation](https://lamport.azurewebsites.net/tla/tla.html)
- [TLA+ Toolbox User Guide](https://lamport.azurewebsites.net/tla/toolbox.html)
- [TLA+ Examples](https://github.com/tlaplus/Examples)

