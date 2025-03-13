import time
import os
import sys
from colorama import init, Fore, Style

init()  # Initialize colorama

class TerminalVisualizer:
    def __init__(self):
        self.devices = {}
        self.messages = []
        self.max_messages = 15
        
    def update_device(self, device_id, status, leader_id=None):
        self.devices[device_id] = {
            'id': device_id,
            'status': status,
            'leader_id': leader_id,
            'last_update': time.time()
        }
        
    def add_message(self, msg_type, from_id, to_id=None, content=None):
        self.messages.append({
            'time': time.time(),
            'type': msg_type,
            'from_id': from_id,
            'to_id': to_id,
            'content': content
        })
        
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
            
    def render(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Print header
        print(f"{Fore.CYAN}===== LEADER-FOLLOWER PROTOCOL VISUALIZATION ====={Style.RESET_ALL}")
        print()
        
        # Print devices section
        print(f"{Fore.YELLOW}DEVICES:{Style.RESET_ALL}")
        print("-" * 50)
        
        for device_id, device in sorted(self.devices.items()):
            status_color = Fore.GREEN if device['status'] == 'LEADER' else Fore.BLUE
            status_str = f"{status_color}{device['status']}{Style.RESET_ALL}"
            
            leader_str = f"Following: {device['leader_id']}" if device['leader_id'] and device['status'] == 'FOLLOWER' else ""
            
            print(f"Device {device_id}: {status_str} {leader_str}")
        
        print("\n")
        
        # Print messages/events
        print(f"{Fore.YELLOW}RECENT PROTOCOL EVENTS:{Style.RESET_ALL}")
        print("-" * 50)
        
        for msg in self.messages[-self.max_messages:]:
            timestamp = time.strftime("%H:%M:%S", time.localtime(msg['time']))
            
            if msg['type'] == 'TIEBREAKER':
                color = Fore.RED
                message = f"TIEBREAKER between {msg['from_id']} and {msg['to_id']}"
            elif msg['type'] == 'LEADER':
                color = Fore.GREEN
                message = f"Device {msg['from_id']} became LEADER"
            elif msg['type'] == 'FOLLOWER':
                color = Fore.BLUE
                message = f"Device {msg['from_id']} became FOLLOWER of {msg['to_id']}"
            elif msg['type'] == 'SEND':
                color = Fore.WHITE
                message = f"Device {msg['from_id']} sent message to {msg['to_id']}"
            elif msg['type'] == 'RECEIVE':
                color = Fore.WHITE
                message = f"Device {msg['to_id']} received message from {msg['from_id']}"
            else:
                color = Fore.WHITE
                message = f"{msg['type']} - {msg['content'] if msg['content'] else ''}"
            
            print(f"{timestamp} {color}{message}{Style.RESET_ALL}")
            
        # Print help
        print("\n")
        print(f"{Fore.CYAN}Commands: (q)uit, (c)reate device, (d)elete device, (t)oggle device{Style.RESET_ALL}")

# Example usage
if __name__ == "__main__":
    viz = TerminalVisualizer()
    
    # Demo data
    viz.update_device(123, 'LEADER')
    viz.update_device(456, 'FOLLOWER', 123)
    viz.add_message('LEADER', 123)
    viz.add_message('FOLLOWER', 456, 123)
    viz.add_message('TIEBREAKER', 123, 456)
    
    # Render the visualization
    viz.render()