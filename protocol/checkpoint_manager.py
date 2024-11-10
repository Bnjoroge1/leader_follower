from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time
import json
import dill
import logging
from pathlib import Path

@dataclass
class CheckpointData:
    timestamp: float
    simulation_id: str
    node_states: Dict[str, Any]
    message_queues: Dict[str, List[Any]]
     

    trace_points: List[str]

class CheckpointManager:
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.trace_points = set()
        self.logger = logging.getLogger("checkpoint_manager")
        
    def create_checkpoint(self, simulation_id: str, nodes: Dict[str, Any]) -> str:
        """Creates a checkpoint of current simulation state"""
        checkpoint_data = CheckpointData(
            timestamp=time.time(),
            simulation_id=simulation_id,
            node_states={},
            message_queues={},
            trace_points=list(self.trace_points)
        )
        print(f"DEBUG: Checkpoint data: {checkpoint_data}")

        for node_id, node in nodes.items():
            checkpoint_data.node_states[node_id] = node.get_checkpoint_state()
            print("adding checkpoint value he: ", checkpoint_data)
            checkpoint_data.message_queues[node_id] = node.get_queue_state()

        checkpoint_path = self._save_checkpoint(checkpoint_data)
        self.logger.info(f"Created checkpoint: {checkpoint_path}")
        return checkpoint_path

    def enable_trace(self, trace_point: str):
        """Add a trace point to watch for"""
        self.trace_points.add(trace_point)

    def disable_trace(self, trace_point: str):
        """Remove a trace point"""
        self.trace_points.discard(trace_point)

    def _save_checkpoint(self, checkpoint_data: CheckpointData) -> str:
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{checkpoint_data.simulation_id}_{int(checkpoint_data.timestamp)}.pkl"
        with open(checkpoint_path, 'wb') as f:
            dill.dump(checkpoint_data, f)
        return str(checkpoint_path)
    
    def restore_checkpoint(self, checkpoint_path: str) -> CheckpointData:
        """Restores simulation state from a checkpoint"""
        try:
            with open(checkpoint_path, 'rb') as f:
                checkpoint_data = dill.load(f)
                self.logger.info(f"Restored checkpoint: {checkpoint_path}")
                return checkpoint_data
        except Exception as e:
            self.logger.error(f"Failed to restore checkpoint: {e}")
            raise

    def list_checkpoints(self) -> List[str]:
        """Lists all available checkpoints"""
        return [str(p) for p in self.checkpoint_dir.glob("checkpoint_*.pkl")]

    def get_latest_checkpoint(self) -> Optional[str]:
        """Gets the most recent checkpoint file"""
        checkpoints = list(self.checkpoint_dir.glob("checkpoint_*.pkl"))
        return str(max(checkpoints, key=lambda p: p.stat().st_mtime)) if checkpoints else None

    def should_checkpoint(self, trace_point: str) -> bool:
        return trace_point in self.trace_points