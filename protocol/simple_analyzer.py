#!/usr/bin/env python3
"""
Simple Protocol Analyzer - Works without matplotlib to analyze existing data
"""

import json
from pathlib import Path
import time

def analyze_protocol_files(heartbeat_file, swim_file, output_dir):
    """Analyze the protocol comparison without matplotlib"""
    
    print("🔍 ANALYZING PROTOCOL COMPARISON DATA")
    print("=" * 60)
    
    # Load data files
    try:
        with open(heartbeat_file) as f:
            hb_data = json.load(f)
        print(f"✅ Loaded heartbeat data: {heartbeat_file}")
        
        with open(swim_file) as f:
            swim_data = json.load(f)
        print(f"✅ Loaded SWIM data: {swim_file}")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Analyze the data
    print(f"\n📊 DATA ANALYSIS RESULTS:")
    
    # Get metrics from the data
    hb_history = hb_data.get('metrics_history', [])
    swim_history = swim_data.get('metrics_history', [])
    
    hb_failures = hb_data.get('failure_events', [])
    swim_failures = swim_data.get('failure_events', [])
    
    print(f"\n📈 METRICS OVERVIEW:")
    print(f"   Heartbeat records: {len(hb_history)}")
    print(f"   SWIM records:      {len(swim_history)}")
    print(f"   Heartbeat failures: {len(hb_failures)}")
    print(f"   SWIM failures:      {len(swim_failures)}")
    
    # Calculate totals
    if hb_history and swim_history:
        # Sum up messages and bytes
        hb_total_msgs = sum(record.get('messages_sent', 0) for record in hb_history)
        swim_total_msgs = sum(record.get('messages_sent', 0) for record in swim_history)
        
        hb_total_bytes = sum(record.get('bytes_sent', 0) for record in hb_history)
        swim_total_bytes = sum(record.get('bytes_sent', 0) for record in swim_history)
        
        # Calculate detection times
        hb_detection_times = [event.get('detection_time', 0) for event in hb_failures if event.get('detection_time', 0) > 0]
        swim_detection_times = [event.get('detection_time', 0) for event in swim_failures if event.get('detection_time', 0) > 0]
        
        hb_avg_detection = sum(hb_detection_times) / len(hb_detection_times) if hb_detection_times else 0
        swim_avg_detection = sum(swim_detection_times) / len(swim_detection_times) if swim_detection_times else 0
        
        print(f"\n📊 COMPARISON RESULTS:")
        print(f"{'Protocol':<12} {'Messages':<10} {'Bytes':<10} {'Avg Detection':<15}")
        print(f"{'-'*12} {'-'*10} {'-'*10} {'-'*15}")
        print(f"{'Heartbeat':<12} {hb_total_msgs:<10} {hb_total_bytes:<10} {hb_avg_detection:.2f}s")
        print(f"{'SWIM':<12} {swim_total_msgs:<10} {swim_total_bytes:<10} {swim_avg_detection:.2f}s")
        
        # Calculate improvements
        if hb_total_msgs > 0:
            msg_reduction = ((hb_total_msgs - swim_total_msgs) / hb_total_msgs) * 100
            byte_reduction = ((hb_total_bytes - swim_total_bytes) / hb_total_bytes) * 100
            time_improvement = hb_avg_detection - swim_avg_detection
            
            print(f"\n🎯 SWIM IMPROVEMENTS:")
            print(f"   💬 Messages reduced by: {msg_reduction:.1f}%")
            print(f"   📡 Bandwidth saved:     {byte_reduction:.1f}%")
            print(f"   ⚡ Detection faster by: {time_improvement:.2f}s")
            
            # Generate text report
            report_content = f"""# Protocol Comparison Analysis

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Data Sources
- Heartbeat: {Path(heartbeat_file).name}
- SWIM: {Path(swim_file).name}

## Results Summary

### Message Efficiency
- **Heartbeat**: {hb_total_msgs:,} messages ({hb_total_bytes:,} bytes)
- **SWIM**: {swim_total_msgs:,} messages ({swim_total_bytes:,} bytes)
- **Improvement**: {msg_reduction:.1f}% fewer messages, {byte_reduction:.1f}% less bandwidth

### Failure Detection Performance
- **Heartbeat**: {hb_avg_detection:.2f}s average detection time
- **SWIM**: {swim_avg_detection:.2f}s average detection time
- **Improvement**: {time_improvement:.2f}s faster detection

### Event Counts
- **Heartbeat failure events**: {len(hb_failures)}
- **SWIM failure events**: {len(swim_failures)}

## Conclusion

{'SWIM protocol demonstrates superior performance with significant reductions in network overhead and faster failure detection.' if msg_reduction > 0 and time_improvement > 0 else 'Results show mixed performance - consider specific requirements.'}

## Raw Data Summary
- **Heartbeat metrics records**: {len(hb_history)}
- **SWIM metrics records**: {len(swim_history)}
- **Analysis timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # Save report
            report_file = Path(output_dir) / "detailed_comparison_analysis.md"
            with open(report_file, 'w') as f:
                f.write(report_content)
            
            print(f"\n✅ Detailed report saved: {report_file}")
            
            return {
                'heartbeat_messages': hb_total_msgs,
                'swim_messages': swim_total_msgs,
                'message_reduction': msg_reduction,
                'bandwidth_reduction': byte_reduction,
                'time_improvement': time_improvement,
                'report_file': str(report_file)
            }
    
    else:
        print("❌ No metrics history found in data files")
        return None

def find_latest_files(output_dir):
    """Find the latest heartbeat and SWIM files"""
    output_path = Path(output_dir)
    
    hb_files = list(output_path.glob("heartbeat_metrics_*.json"))
    swim_files = list(output_path.glob("swim_metrics_*.json"))
    
    if hb_files:
        hb_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    if swim_files:
        swim_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return hb_files[0] if hb_files else None, swim_files[0] if swim_files else None

def main():
    output_dir = "./output"
    
    print("🚀 SIMPLE PROTOCOL ANALYZER")
    print("Analyzing your existing protocol comparison data")
    
    # Find latest files
    hb_file, swim_file = find_latest_files(output_dir)
    
    if not hb_file or not swim_file:
        print(f"❌ Could not find both heartbeat and SWIM files in {output_dir}")
        print(f"   Heartbeat file: {'✅' if hb_file else '❌'} {hb_file or 'Not found'}")
        print(f"   SWIM file: {'✅' if swim_file else '❌'} {swim_file or 'Not found'}")
        return
    
    print(f"📁 Using files:")
    print(f"   Heartbeat: {hb_file}")
    print(f"   SWIM: {swim_file}")
    
    # Analyze the files
    results = analyze_protocol_files(hb_file, swim_file, output_dir)
    
    if results:
        print(f"\n✨ ANALYSIS COMPLETE!")
        print(f"   Check {results['report_file']} for detailed results")
        print(f"   SWIM shows {results['message_reduction']:.1f}% message reduction")
        print(f"   and {results['time_improvement']:.2f}s faster detection")

if __name__ == "__main__":
    main() 