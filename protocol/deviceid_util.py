import uuid
import os
import json
from pathlib import Path
import logging

def get_mac_address():
    """Get the MAC address of the primary network interface"""
    try:
        # Try platform-specific methods to get MAC address
        import platform
        
        if platform.system() == "Windows":
            import subprocess
            output = subprocess.check_output("getmac /fo csv /nh").decode().strip()
            mac = output.split(',')[0].strip('"')
            return mac
        elif platform.system() == "Darwin" or platform.system() == "Linux":
            import uuid
            import re
            # Get all network interfaces
            from uuid import getnode
            mac = ':'.join(re.findall('..', '%012x' % getnode()))
            return mac
    except Exception as e:
        logging.warning(f"Could not get MAC address: {e}")
        return None

def generate_persistent_device_id(storage_dir="device_ids"):
    """Generate a persistent device ID using UUID"""
    

print(generate_persistent_device_id())