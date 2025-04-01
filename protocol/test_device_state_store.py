import unittest
from pathlib import Path
import shutil
import json
from device_state import DeviceStateStore

class TestDeviceStateStore(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for testing"""
        self.test_dir = Path("test_device_states")
        self.store = DeviceStateStore(state_dir=str(self.test_dir))
    
    def tearDown(self):
        """Clean up the temporary directory"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_save_and_retrieve_state(self):
        """Test saving and retrieving a device state"""
        device_id = 1
        state = {
            "device_id": device_id,
            "device_uuid": "test-uuid",
            "task": 42
        }
        self.store.save_device_state(device_id, state)
        retrieved_state = self.store.get_latest_device_state(device_id)
        self.assertEqual(state, retrieved_state)
    
    def test_find_states_by_uuid_hash(self):
        """Test finding states by UUID hash"""
        device_id = 1
        uuid = "test-uuid"
        state = {
            "device_id": device_id,
            "device_uuid": uuid,
            "task": 42
        }
        self.store.save_device_state(device_id, state)
        uuid_hash = abs(hash(uuid)) % 100000
        matching_states = self.store.find_states_by_uuid_hash(uuid_hash)
        self.assertEqual(len(matching_states), 1)
        self.assertEqual(matching_states[0]["device_uuid"], uuid)
    
    def test_update_device_id(self):
        """Test updating device ID in state files"""
        old_id = 1
        new_id = 2
        state = {
            "device_id": old_id,
            "device_uuid": "test-uuid",
            "task": 42
        }
        self.store.save_device_state(old_id, state)
        self.store.update_device_id(old_id, new_id)
        updated_state = self.store.get_latest_device_state(new_id)
        self.assertIsNotNone(updated_state)
        self.assertEqual(updated_state["device_id"], new_id)

if __name__ == "__main__":
    unittest.main()