#!/usr/bin/env python3
"""
Graph Results - Create visualizations of protocol comparison results
"""

import json
from pathlib import Path
import time

def create_text_graphs(hb_data, swim_data):
    """Create text-based graphs for the terminal"""
    
    print("📊 TEXT-BASED GRAPHS")
    print("=" * 60)
    
    # Extract data
    hb_history = hb_data.get('metrics_history', [])
    swim_history = swim_data.get('metrics_history', [])
    
    if not hb_history or not swim_history:
        print("❌ No data to graph")
        return
    
    # Calculate totals
    hb_total_msgs = sum(record.get('messages_sent', 0) for record in hb_history)
    swim_total_msgs = sum(record.get('messages_sent', 0) for record in swim_history)
    
    hb_total_bytes = sum(record.get('bytes_sent', 0) for record in hb_history)
    swim_total_bytes = sum(record.get('bytes_sent', 0) for record in swim_history)
    
    hb_failures = hb_data.get('failure_events', [])
    swim_failures = swim_data.get('failure_events', [])
    
    hb_detection_times = [event.get('detection_time', 0) for event in hb_failures if event.get('detection_time', 0) > 0]
    swim_detection_times = [event.get('detection_time', 0) for event in swim_failures if event.get('detection_time', 0) > 0]
    
    hb_avg_detection = sum(hb_detection_times) / len(hb_detection_times) if hb_detection_times else 0
    swim_avg_detection = sum(swim_detection_times) / len(swim_detection_times) if swim_detection_times else 0
    
    # 1. Messages Comparison Bar Chart
    print("\n📈 MESSAGES SENT COMPARISON")
    print("-" * 40)
    max_msgs = max(hb_total_msgs, swim_total_msgs)
    hb_bar_len = int((hb_total_msgs / max_msgs) * 30) if max_msgs > 0 else 0
    swim_bar_len = int((swim_total_msgs / max_msgs) * 30) if max_msgs > 0 else 0
    
    print(f"Heartbeat: {'█' * hb_bar_len:<30} {hb_total_msgs}")
    print(f"SWIM:      {'█' * swim_bar_len:<30} {swim_total_msgs}")
    
    # 2. Bandwidth Comparison
    print("\n📡 BANDWIDTH USAGE COMPARISON")
    print("-" * 40)
    max_bytes = max(hb_total_bytes, swim_total_bytes)
    hb_byte_bar = int((hb_total_bytes / max_bytes) * 30) if max_bytes > 0 else 0
    swim_byte_bar = int((swim_total_bytes / max_bytes) * 30) if max_bytes > 0 else 0
    
    print(f"Heartbeat: {'█' * hb_byte_bar:<30} {hb_total_bytes:,} bytes")
    print(f"SWIM:      {'█' * swim_byte_bar:<30} {swim_total_bytes:,} bytes")
    
    # 3. Detection Time Comparison
    print("\n⚡ FAILURE DETECTION TIME COMPARISON")
    print("-" * 40)
    max_time = max(hb_avg_detection, swim_avg_detection) if hb_avg_detection > 0 and swim_avg_detection > 0 else 3.0
    hb_time_bar = int((hb_avg_detection / max_time) * 30) if max_time > 0 else 0
    swim_time_bar = int((swim_avg_detection / max_time) * 30) if max_time > 0 else 0
    
    print(f"Heartbeat: {'█' * hb_time_bar:<30} {hb_avg_detection:.2f}s")
    print(f"SWIM:      {'█' * swim_time_bar:<30} {swim_avg_detection:.2f}s")
    print("           (Lower is better)")
    
    # 4. Message Timeline
    print("\n📊 MESSAGE ACTIVITY OVER TIME")
    print("-" * 40)
    
    # Group by time windows
    time_windows = 6  # Show 6 time periods
    hb_msgs_per_window = []
    swim_msgs_per_window = []
    
    for i in range(time_windows):
        start_idx = i * len(hb_history) // time_windows
        end_idx = (i + 1) * len(hb_history) // time_windows
        
        hb_window_msgs = sum(record.get('messages_sent', 0) for record in hb_history[start_idx:end_idx])
        swim_window_msgs = sum(record.get('messages_sent', 0) for record in swim_history[start_idx:end_idx])
        
        hb_msgs_per_window.append(hb_window_msgs)
        swim_msgs_per_window.append(swim_window_msgs)
    
    max_window_msgs = max(max(hb_msgs_per_window), max(swim_msgs_per_window)) if hb_msgs_per_window and swim_msgs_per_window else 1
    
    print("Time →  1     2     3     4     5     6")
    print("HB:   ", end="")
    for msgs in hb_msgs_per_window:
        bar_height = int((msgs / max_window_msgs) * 5) if max_window_msgs > 0 else 0
        print(f"{'█' * bar_height:<6}", end="")
    print(f" (Total: {sum(hb_msgs_per_window)})")
    
    print("SWIM: ", end="")
    for msgs in swim_msgs_per_window:
        bar_height = int((msgs / max_window_msgs) * 5) if max_window_msgs > 0 else 0
        print(f"{'█' * bar_height:<6}", end="")
    print(f" (Total: {sum(swim_msgs_per_window)})")
    
    # 5. Summary Statistics
    print("\n📋 SUMMARY STATISTICS")
    print("-" * 40)
    msg_diff = ((hb_total_msgs - swim_total_msgs) / hb_total_msgs * 100) if hb_total_msgs > 0 else 0
    byte_diff = ((hb_total_bytes - swim_total_bytes) / hb_total_bytes * 100) if hb_total_bytes > 0 else 0
    time_diff = hb_avg_detection - swim_avg_detection
    
    print(f"Message efficiency:  {'SWIM wins' if msg_diff > 0 else 'Heartbeat wins'} by {abs(msg_diff):.1f}%")
    print(f"Bandwidth efficiency: {'SWIM wins' if byte_diff > 0 else 'Heartbeat wins'} by {abs(byte_diff):.1f}%")
    print(f"Detection speed:     {'SWIM wins' if time_diff > 0 else 'Heartbeat wins'} by {abs(time_diff):.2f}s")
    print(f"Failure events:      HB: {len(hb_failures)}, SWIM: {len(swim_failures)}")

def create_matplotlib_code():
    """Generate Python code for creating proper matplotlib graphs"""
    
    code = '''
# MATPLOTLIB GRAPH CODE (run when matplotlib is available)
# Save this as create_graphs.py and run: python3 create_graphs.py

import matplotlib.pyplot as plt
import json
import numpy as np
from pathlib import Path

def load_data():
    with open('output/heartbeat_metrics_1753649618.json') as f:
        hb_data = json.load(f)
    with open('output/swim_metrics_1753649618.json') as f:
        swim_data = json.load(f)
    return hb_data, swim_data

def create_comparison_graphs():
    hb_data, swim_data = load_data()
    
    # Extract metrics
    hb_history = hb_data.get('metrics_history', [])
    swim_history = swim_data.get('metrics_history', [])
    hb_failures = hb_data.get('failure_events', [])
    swim_failures = swim_data.get('failure_events', [])
    
    # Calculate totals
    hb_total_msgs = sum(r.get('messages_sent', 0) for r in hb_history)
    swim_total_msgs = sum(r.get('messages_sent', 0) for r in swim_history)
    hb_total_bytes = sum(r.get('bytes_sent', 0) for r in hb_history)
    swim_total_bytes = sum(r.get('bytes_sent', 0) for r in swim_history)
    
    hb_detection_times = [e.get('detection_time', 0) for e in hb_failures if e.get('detection_time', 0) > 0]
    swim_detection_times = [e.get('detection_time', 0) for e in swim_failures if e.get('detection_time', 0) > 0]
    hb_avg_detection = np.mean(hb_detection_times) if hb_detection_times else 0
    swim_avg_detection = np.mean(swim_detection_times) if swim_detection_times else 0
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Protocol Comparison: Heartbeat vs SWIM', fontsize=16)
    
    # 1. Messages comparison
    protocols = ['Heartbeat', 'SWIM']
    messages = [hb_total_msgs, swim_total_msgs]
    ax1.bar(protocols, messages, color=['#ff7f0e', '#1f77b4'])
    ax1.set_title('Total Messages Sent')
    ax1.set_ylabel('Messages')
    for i, v in enumerate(messages):
        ax1.text(i, v + max(messages)*0.01, str(v), ha='center')
    
    # 2. Bandwidth comparison
    bandwidth = [hb_total_bytes/1024, swim_total_bytes/1024]  # Convert to KB
    ax2.bar(protocols, bandwidth, color=['#ff7f0e', '#1f77b4'])
    ax2.set_title('Total Bandwidth Usage')
    ax2.set_ylabel('Kilobytes')
    for i, v in enumerate(bandwidth):
        ax2.text(i, v + max(bandwidth)*0.01, f'{v:.1f}KB', ha='center')
    
    # 3. Detection time comparison
    detection_times = [hb_avg_detection, swim_avg_detection]
    ax3.bar(protocols, detection_times, color=['#ff7f0e', '#1f77b4'])
    ax3.set_title('Average Failure Detection Time')
    ax3.set_ylabel('Seconds')
    for i, v in enumerate(detection_times):
        ax3.text(i, v + max(detection_times)*0.01, f'{v:.2f}s', ha='center')
    
    # 4. Message timeline
    time_points = range(len(hb_history))
    hb_msgs_timeline = [r.get('messages_sent', 0) for r in hb_history]
    swim_msgs_timeline = [r.get('messages_sent', 0) for r in swim_history]
    
    ax4.plot(time_points, hb_msgs_timeline, label='Heartbeat', color='#ff7f0e', marker='o')
    ax4.plot(time_points, swim_msgs_timeline, label='SWIM', color='#1f77b4', marker='s')
    ax4.set_title('Messages Over Time')
    ax4.set_xlabel('Time Period')
    ax4.set_ylabel('Messages')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('output/protocol_comparison_graphs.png', dpi=300, bbox_inches='tight')
    print("✅ Graphs saved to output/protocol_comparison_graphs.png")
    plt.show()

if __name__ == "__main__":
    create_comparison_graphs()
'''
    
    return code

def main():
    print("📊 GRAPHING PROTOCOL COMPARISON RESULTS")
    print("=" * 60)
    
    # Find data files
    output_dir = Path("./output")
    hb_files = list(output_dir.glob("heartbeat_metrics_*.json"))
    swim_files = list(output_dir.glob("swim_metrics_*.json"))
    
    if not hb_files or not swim_files:
        print("❌ No data files found")
        return
    
    # Use latest files
    hb_file = sorted(hb_files, key=lambda x: x.stat().st_mtime)[-1]
    swim_file = sorted(swim_files, key=lambda x: x.stat().st_mtime)[-1]
    
    print(f"📁 Using data files:")
    print(f"   Heartbeat: {hb_file.name}")
    print(f"   SWIM: {swim_file.name}")
    
    # Load data
    try:
        with open(hb_file) as f:
            hb_data = json.load(f)
        with open(swim_file) as f:
            swim_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Create text graphs
    create_text_graphs(hb_data, swim_data)
    
    # Generate matplotlib code
    print(f"\n🎨 MATPLOTLIB GRAPH CODE")
    print("=" * 60)
    print("To create proper graphs, save the following code as 'create_graphs.py'")
    print("and run it when matplotlib is available:")
    
    matplotlib_code = create_matplotlib_code()
    
    # Save the matplotlib code
    code_file = output_dir / "create_graphs.py"
    with open(code_file, 'w') as f:
        f.write(matplotlib_code)
    
    print(f"✅ Matplotlib code saved to: {code_file}")
    print(f"\nTo use it:")
    print(f"1. Install matplotlib: pip install matplotlib")
    print(f"2. Run: python3 {code_file}")
    print(f"3. Graphs will be saved as: output/protocol_comparison_graphs.png")

if __name__ == "__main__":
    main() 