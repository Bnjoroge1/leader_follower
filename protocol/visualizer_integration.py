from terminal_visualizer import TerminalVisualizer
import threading
import time

class VisualizerIntegrator:
    def __init__(self):
        self.visualizer = TerminalVisualizer()
        self.running = False
        self.update_thread = None
        
    def start(self):
        """Start the visualizer and update thread"""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def stop(self):
        """Stop the visualizer update thread"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def _update_loop(self):
        """Background thread to periodically update and render the visualization"""
        while self.running:
            self.update_devices_from_logs()
            self.visualizer.render()
            time.sleep(1)  # Update every second
    
    def update_devices_from_logs(self):
        """Parse device logs to update the visualizer state"""
        # Look for log files in the output directory
        import glob
        import csv
        from pathlib import Path
        
        log_files = glob.glob('protocol/output/device_log_*.csv')
        
        for log_file in log_files:
            device_id = int(Path(log_file).stem.split('_')[2])  # Extract device ID from filename
            
            # Read the last few lines of the log file to get current state
            try:
                with open(log_file, 'r') as f:
                    # Read the last 50 lines (adjust as needed)
                    lines = list(csv.reader(f))[-50:]
                    
                    # Process lines to determine device state
                    leader_status = False
                    follower_status = False
                    leader_id = None
                    
                    for line in reversed(lines):  # Start from most recent
                        if len(line) < 3:
                            continue
                            
                        timestamp, msg_type, content = line[0], line[1], line[2]
                        
                        # Check for leader/follower status
                        if msg_type == "STATUS":
                            if content == "BECAME LEADER":
                                leader_status = True
                                break
                            elif "BECAME FOLLOWER OF" in content:
                                follower_status = True
                                try:
                                    leader_id = int(content.split()[-1])
                                    break
                                except ValueError:
                                    pass
                
                    # Update visualizer with device state
                    if leader_status:
                        self.visualizer.update_device(device_id, "LEADER")
                    elif follower_status and leader_id is not None:
                        self.visualizer.update_device(device_id, "FOLLOWER", leader_id)
                        
                    # Also scan for recent messages/events to display
                    for line in reversed(lines):
                        if len(line) < 3:
                            continue
                            
                        timestamp, msg_type, content = line[0], line[1], line[2]
                        
                        # Add message events
                        if msg_type == "MSG SEND":
                            msg_code = int(content)
                            action = msg_code // int(1e10)
                            if action == 1:  # ATTENDANCE
                                self.visualizer.add_message("SEND", device_id, 0, "ATTENDANCE")
                            elif action == 4:  # CHECK_IN
                                follower_id = msg_code % int(1e4)
                                self.visualizer.add_message("SEND", device_id, follower_id, "CHECK-IN")
                        
                        # Add status events
                        elif msg_type == "STATUS":
                            if "HEARD OTHER LEADER" in content:
                                try:
                                    other_leader = int(content.split()[-1])
                                    self.visualizer.add_message("TIEBREAKER", device_id, other_leader)
                                except ValueError:
                                    pass
                            elif content == "BECAME LEADER":
                                self.visualizer.add_message("LEADER", device_id)
                            elif "BECAME FOLLOWER OF" in content:
                                try:
                                    leader_id = int(content.split()[-1])
                                    self.visualizer.add_message("FOLLOWER", device_id, leader_id)
                                except ValueError:
                                    pass
                                    
            except Exception as e:
                print(f"Error processing log file {log_file}: {e}")

# Usage example
def main():
    integrator = VisualizerIntegrator()
    
    try:
        integrator.start()
        
        # Keep the main thread running
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down visualizer...")
    finally:
        integrator.stop()

if __name__ == "__main__":
    main()