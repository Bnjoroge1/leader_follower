from dataclasses import dataclass
from operator import index
from pathlib import Path
import logging
from typing import Any, List, Set
import time
import json

@dataclass
class DeviceState:
     
     device_list:List
     device_uuid: str
     known_leaders:Set
     is_leader:bool
     missed:int
     task:int
     current_leader:int
     received:int 
     device_id:int 
     


class DeviceStateStore:
     def __init__(self, state_dir:str = None):
          if not state_dir :
               state_dir = Path(__file__).parent / "DeviceState"  # 
          else:
               state_dir = Path(state_dir)

          self.state_dir = state_dir
          self.state_dir.mkdir(parents=True, exist_ok=True)
          self.logger = logging.getLogger("devicestate_store")
          
     def save_device_state(self, device_id, state_dict):
          """save device state with timestamp for versioning"""
          timestamp = int(time.time())
          filename = f"devicestate_{device_id}-{timestamp}.json"
          filepath = self.state_dir / filename
 
          with open(filepath, "w") as file:
               json.dump(state_dict, file, indent=2)
          
          self._cleanup_old_states(device_id)

          return str(filepath)
     
     def _cleanup_old_states(self, device_id, keep=5):
          """
          keep the most recent 5 files
          """
          files = sorted(
               self.state_dir.glob(f"device_{device_id}_*.json"),
               key = lambda p: p.stat().st_mtime,
               reverse=True
          )
          for old_file in files[keep:]:
               old_file.unlink()

     def get_latest_device_state(self, device_id):
          """Retrieve most recent state for a specific device"""
          files = sorted(
               self.state_dir.glob(f"devicestate_{device_id}-*.json"),
               key=lambda p: p.stat().st_mtime,
               reverse=True
          )
          
          if not files:
               return None
               
          latest_file = files[0]
          with open(latest_file, 'r') as f:
               return json.load(f)
     def find_states_by_uuid_hash(self, uuid_hash):
          """Find device states matching a UUID hash fingerprint"""
          matching_states = []
          files = self.state_dir.glob("devicestate_*.json")
          for file in files:
               try:
                    with open(file, "r") as f:
                         state = json.load(f)
                         if "device_uuid" in state:
                              #calcualte hash 
                              state_hash = abs(hash(state["device_uuid"])) % 100000
                              if state_hash == uuid_hash:
                                   matching_states.append(state)
               except (json.JSONDecodeError, KeyError):
                    continue
          return matching_states

     # Add this for migration between device IDs
     def update_device_id(self, old_id, new_id):
          """Update device ID in state files when it changes"""
          files = self.state_dir.glob(f"devicestate_{old_id}-*.json")
          
          for file in files:
               try:
                    with open(file, "r") as f:
                         state = json.load(f)
                    
                    # Update device ID
                    state["device_id"] = new_id
                    
                    # Save with new ID
                    new_filename = f"devicestate_{new_id}-{int(time.time())}.json"
                    new_path = self.state_dir / new_filename
                    
                    with open(new_path, "w") as f:
                         json.dump(state, f, indent=2)
                    
                    # Optionally delete old file
                    file.unlink()
                         
               except (json.JSONDecodeError, KeyError):
                    continue
          
