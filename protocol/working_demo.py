#!/usr/bin/env python3
"""
Working Demo - Shows exactly where your results are and what they contain
"""

import json
import time
from pathlib import Path

def show_current_results():
    """Show what results are already available"""
    output_dir = Path("./output")
    
    print("🎯 CURRENT RESULTS IN OUTPUT DIRECTORY")
    print("=" * 60)
    print(f"📁 Location: {output_dir.absolute()}")
    
    if not output_dir.exists():
        print("❌ Output directory doesn't exist yet")
        return
    
    # List all files
    files = list(output_dir.glob("*"))
    if not files:
        print("❌ No result files found yet")
        return
    
    # Sort by newest first
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"\n📊 AVAILABLE RESULT FILES:")
    for i, file in enumerate(files[:10]):  # Show newest 10
        if file.is_file():
            size = file.stat().st_size
            size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
            modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file.stat().st_mtime))
            
            if 'heartbeat' in file.name and file.suffix == '.json':
                print(f"   {i+1}. 📊 {file.name} ({size_str}) - Heartbeat data [{modified}]")
            elif 'swim' in file.name and file.suffix == '.json':
                print(f"   {i+1}. 📊 {file.name} ({size_str}) - SWIM data [{modified}]")
            elif file.suffix == '.md':
                print(f"   {i+1}. 📄 {file.name} ({size_str}) - Analysis report [{modified}]")
            else:
                print(f"   {i+1}. 📄 {file.name} ({size_str}) [{modified}]")
    
    # Show sample of newest metrics file
    json_files = [f for f in files if f.suffix == '.json' and ('heartbeat' in f.name or 'swim' in f.name)]
    if json_files:
        newest_file = json_files[0]
        print(f"\n📋 SAMPLE DATA FROM {newest_file.name}:")
        try:
            with open(newest_file) as f:
                data = json.load(f)
            
            # Show structure
            print(f"   📈 Data structure:")
            for key in data.keys():
                if isinstance(data[key], list):
                    print(f"      • {key}: {len(data[key])} items")
                elif isinstance(data[key], dict):
                    print(f"      • {key}: {len(data[key])} entries")
                else:
                    print(f"      • {key}: {type(data[key]).__name__}")
            
            # Show sample metrics
            if 'metrics_history' in data and data['metrics_history']:
                sample = data['metrics_history'][0]
                print(f"   📊 Sample metrics record:")
                for key, value in list(sample.items())[:8]:  # Show first 8 fields
                    print(f"      • {key}: {value}")
                if len(sample) > 8:
                    print(f"      • ... and {len(sample) - 8} more fields")
                    
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

def show_how_to_get_real_results():
    """Show user how to generate real results"""
    print(f"\n🚀 HOW TO GET REAL RESULTS:")
    print("=" * 60)
    
    print(f"📝 OPTION 1: Use Your Existing System")
    print(f"   1. Switch to heartbeat: python3 -c \"from protocol_config import switch_protocol; switch_protocol('heartbeat')\"")
    print(f"   2. Run your simulation: python3 channel_driver.py")
    print(f"   3. Let it run for 30+ seconds, then stop (Ctrl+C)")
    print(f"   4. Switch to SWIM: python3 -c \"from protocol_config import switch_protocol; switch_protocol('swim')\"")
    print(f"   5. Run simulation again: python3 channel_driver.py")
    print(f"   6. Let it run for same duration, then stop")
    print(f"   7. Results will be in: ./output/")
    
    print(f"\n📝 OPTION 2: Use Demo Data Generator")
    print(f"   1. Run: python3 demo_results.py")
    print(f"   2. This creates sample data showing expected format")
    print(f"   3. Check: ./output/ for generated files")
    
    print(f"\n📝 OPTION 3: Check Current Configuration")
    print(f"   Current protocol setting:")
    try:
        from protocol_config import get_config_manager
        config = get_config_manager()
        current = config.get_current_protocol()
        print(f"   ✅ Protocol: {current}")
        print(f"   📋 Config file: protocol_config.json")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def show_analysis_commands():
    """Show commands for analyzing results"""
    print(f"\n🔍 HOW TO ANALYZE RESULTS:")
    print("=" * 60)
    
    output_dir = Path("./output")
    json_files = list(output_dir.glob("*.json"))
    hb_files = [f for f in json_files if 'heartbeat' in f.name]
    swim_files = [f for f in json_files if 'swim' in f.name]
    
    print(f"📊 VIEW RAW DATA:")
    if hb_files:
        print(f"   • Heartbeat: cat {hb_files[0]} | head -20")
    if swim_files:
        print(f"   • SWIM: cat {swim_files[0]} | head -20")
    
    print(f"\n📄 VIEW REPORTS:")
    md_files = list(output_dir.glob("*.md"))
    if md_files:
        for md_file in md_files[:3]:
            print(f"   • cat {md_file}")
    else:
        print(f"   • No analysis reports found yet")
    
    print(f"\n📈 GENERATE GRAPHS (when matplotlib available):")
    if hb_files and swim_files:
        print(f"   python3 -c \"from protocol_analyzer import run_protocol_comparison; from pathlib import Path; run_protocol_comparison('{hb_files[0]}', '{swim_files[0]}', Path('./output'))\"")
    else:
        print(f"   • Need both heartbeat and SWIM data files first")
    
    print(f"\n🖥️  OPEN IN FINDER/EXPLORER:")
    print(f"   • macOS: open {output_dir}")
    print(f"   • Linux: xdg-open {output_dir}")
    print(f"   • Windows: explorer {output_dir}")

def main():
    print("🎯 PROTOCOL RESULTS LOCATION GUIDE")
    print("This shows you exactly where to find your results")
    
    # Show current results
    show_current_results()
    
    # Show how to get real results
    show_how_to_get_real_results()
    
    # Show analysis commands
    show_analysis_commands()
    
    print(f"\n✨ SUMMARY:")
    print(f"   📁 All results go to: ./output/")
    print(f"   📊 Data files: *.json (raw metrics)")
    print(f"   📄 Reports: *.md (analysis)")
    print(f"   📈 Graphs: *.png (when matplotlib works)")
    print(f"   🔧 Configuration: protocol_config.json")

if __name__ == "__main__":
    main() 