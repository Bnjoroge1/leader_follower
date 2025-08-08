#!/usr/bin/env python3
"""
Demo Results Generator - Shows you exactly where to find protocol comparison results
"""

import json
import time
from pathlib import Path

def create_sample_results():
    """Create sample results to show you the format and location"""
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    print("🎯 SWIM Protocol Results Location Demo")
    print("=" * 50)
    
    # 1. Create sample heartbeat metrics
    heartbeat_data = {
        "metrics_history": [
            {
                "timestamp": time.time(),
                "protocol_type": "heartbeat",
                "node_id": 1,
                "messages_sent": 150,
                "messages_received": 145,
                "bytes_sent": 12000,
                "bytes_received": 11600,
                "message_latency": 0.8,
                "detection_time": 2.5
            },
            {
                "timestamp": time.time(),
                "protocol_type": "heartbeat", 
                "node_id": 2,
                "messages_sent": 148,
                "messages_received": 142,
                "bytes_sent": 11800,
                "bytes_received": 11400,
                "message_latency": 0.9,
                "detection_time": 2.3
            }
        ],
        "failure_events": [
            {
                "timestamp": time.time(),
                "detector_id": 1,
                "failed_node_id": 3,
                "detection_time": 2.5,
                "is_actual_failure": True,
                "is_false_positive": False
            }
        ],
        "summary": {
            "heartbeat": {
                "total_messages_sent": 298,
                "avg_detection_time": 2.4,
                "total_false_positives": 2,
                "avg_message_latency": 0.85
            }
        }
    }
    
    # 2. Create sample SWIM metrics
    swim_data = {
        "metrics_history": [
            {
                "timestamp": time.time(),
                "protocol_type": "swim",
                "node_id": 1,
                "messages_sent": 75,  # SWIM sends fewer messages
                "messages_received": 73,
                "bytes_sent": 6000,   # Less bandwidth usage
                "bytes_received": 5800,
                "message_latency": 0.5,
                "detection_time": 1.2  # Faster detection
            },
            {
                "timestamp": time.time(),
                "protocol_type": "swim",
                "node_id": 2,
                "messages_sent": 78,
                "messages_received": 71,
                "bytes_sent": 6200,
                "bytes_received": 5600,
                "message_latency": 0.6,
                "detection_time": 1.1
            }
        ],
        "failure_events": [
            {
                "timestamp": time.time(),
                "detector_id": 1,
                "failed_node_id": 3,
                "detection_time": 1.15,
                "is_actual_failure": True,
                "is_false_positive": False
            }
        ],
        "summary": {
            "swim": {
                "total_messages_sent": 153,
                "avg_detection_time": 1.15,
                "total_false_positives": 1,
                "avg_message_latency": 0.55
            }
        }
    }
    
    # 3. Save sample data files
    heartbeat_file = output_dir / "heartbeat_metrics_sample.json"
    swim_file = output_dir / "swim_metrics_sample.json"
    
    with open(heartbeat_file, 'w') as f:
        json.dump(heartbeat_data, f, indent=2)
    
    with open(swim_file, 'w') as f:
        json.dump(swim_data, f, indent=2)
    
    print(f"✅ Created sample metrics files:")
    print(f"   📋 {heartbeat_file}")
    print(f"   📋 {swim_file}")
    
    # 4. Create sample analysis report
    report_content = """# Protocol Comparison Report

Generated on: 2024-12-19 12:00:00

## Executive Summary

This report compares the performance of Heartbeat and SWIM failure detection protocols.

### Key Findings

- **Message Efficiency**: SWIM reduces network messages by 48.7%
- **Detection Speed**: SWIM detects failures 1.25s faster
- **Bandwidth Savings**: SWIM uses 50.0% less bandwidth
- **Accuracy**: Heartbeat 95.2% vs SWIM 97.1%

## Detailed Metrics

### Heartbeat Protocol
- **Messages Sent**: 298
- **Bytes Transmitted**: 23,800
- **Average Detection Time**: 2.40s
- **False Positive Rate**: 5.2%

### SWIM Protocol
- **Messages Sent**: 153
- **Bytes Transmitted**: 12,200
- **Average Detection Time**: 1.15s
- **False Positive Rate**: 2.9%

## Recommendation

The SWIM protocol demonstrates clear advantages over traditional heartbeat mechanisms in terms of efficiency, speed, and scalability.
"""
    
    report_file = output_dir / "protocol_comparison_report.md"
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"   📄 {report_file}")
    
    # 5. Show where graphs would be generated
    graph_files = [
        "protocol_comparison_messages.png",
        "protocol_comparison_failure_detection.png", 
        "protocol_comparison_network.png",
        "protocol_comparison_accuracy.png",
        "protocol_comparison_dashboard.png"
    ]
    
    print(f"\n📈 Graph files would be generated at:")
    for graph_file in graph_files:
        print(f"   🖼️  {output_dir / graph_file}")
    
    # 6. Show directory structure
    print(f"\n📁 COMPLETE RESULTS LOCATION:")
    print(f"   {output_dir.absolute()}")
    print(f"\n📊 File Types You'll Get:")
    print(f"   📋 *.json files - Raw metrics data")
    print(f"   📄 *.md files - Analysis reports") 
    print(f"   📈 *.png files - Graphs and charts")
    
    # 7. Show how to access results
    print(f"\n💡 HOW TO VIEW RESULTS:")
    print(f"   • Raw data: Open .json files in any text editor")
    print(f"   • Reports: Open .md files in text editor or markdown viewer")
    print(f"   • Graphs: Open .png files in image viewer")
    print(f"   • Web browser: Some markdown viewers render .md files nicely")
    
    # 8. Show sample analysis
    print(f"\n🔍 SAMPLE ANALYSIS:")
    hb_msgs = heartbeat_data["summary"]["heartbeat"]["total_messages_sent"]
    swim_msgs = swim_data["summary"]["swim"]["total_messages_sent"]
    reduction = ((hb_msgs - swim_msgs) / hb_msgs) * 100
    
    hb_time = heartbeat_data["summary"]["heartbeat"]["avg_detection_time"]
    swim_time = swim_data["summary"]["swim"]["avg_detection_time"]
    time_improvement = hb_time - swim_time
    
    print(f"   💬 SWIM reduces messages by {reduction:.1f}%")
    print(f"   ⚡ SWIM detects failures {time_improvement:.2f}s faster")
    print(f"   🎯 SWIM has better accuracy (fewer false positives)")
    
    return output_dir

def show_real_usage():
    """Show how to get real results with your actual system"""
    print(f"\n🚀 TO GET REAL RESULTS WITH YOUR SYSTEM:")
    print(f"=" * 50)
    
    print(f"1️⃣  Switch to heartbeat protocol:")
    print(f"    python3 -c \"from protocol_config import switch_protocol; switch_protocol('heartbeat')\"")
    
    print(f"\n2️⃣  Run your existing simulation:")
    print(f"    python3 channel_driver.py")
    print(f"    # Let it run for a while, then stop it")
    
    print(f"\n3️⃣  Switch to SWIM protocol:")
    print(f"    python3 -c \"from protocol_config import switch_protocol; switch_protocol('swim')\"")
    
    print(f"\n4️⃣  Run simulation again:")
    print(f"    python3 channel_driver.py")
    print(f"    # Let it run for same duration")
    
    print(f"\n5️⃣  Generate comparison (when matplotlib is available):")
    print(f"    python3 -c \"from protocol_analyzer import run_protocol_comparison; from pathlib import Path; run_protocol_comparison('heartbeat_metrics.json', 'swim_metrics.json', Path('./output'))\"")
    
    print(f"\n📌 CURRENT STATUS:")
    try:
        from protocol_config import get_config_manager
        config = get_config_manager().get_current_protocol()
        print(f"    Current protocol: {config}")
    except Exception as e:
        print(f"    Config check failed: {e}")

if __name__ == "__main__":
    output_dir = create_sample_results()
    show_real_usage()
    
    print(f"\n✨ Check the output directory for sample files:")
    print(f"   ls -la {output_dir}") 