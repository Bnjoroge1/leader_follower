#!/bin/bash

echo "🚀 SWIM vs Heartbeat Protocol Comparison"
echo "========================================"

# Setup environment - use the same virtual environment
export PYTHONPATH=$PYTHONPATH:$(pwd)
if [ -d ".venv" ]; then
    echo "📦 Activating .venv virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "📦 Activating venv virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install matplotlib seaborn pandas numpy psutil > /dev/null 2>&1

# Clean previous results
echo "🧹 Cleaning previous results..."
rm -f output/heartbeat_metrics_*.json
rm -f output/swim_metrics_*.json
rm -f output/*comparison*.md
rm -f output/*.png

echo ""
echo "🔥 PHASE 1: HEARTBEAT PROTOCOL TEST (60s)"
echo "========================================"

# Run heartbeat test
python3 -c "
import sys; sys.path.append('.')
try:
    from protocol_config import switch_protocol
    from simple_test_runner import SimpleProtocolTester
    from pathlib import Path
    
    print('⚙️  Switching to heartbeat protocol...')
    switch_protocol('heartbeat')
    
    print('🚀 Starting heartbeat test...')
    tester = SimpleProtocolTester(Path('./output'))
    result = tester.run_heartbeat_test(duration=60)
    print(f'✅ Heartbeat test completed! Results: {result}')
    
except Exception as e:
    print(f'❌ Error in heartbeat test: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "🏊 PHASE 2: SWIM PROTOCOL TEST (60s)"
echo "===================================="
    
# Run SWIM test
python3 -c "
import sys; sys.path.append('.')
try:
    from protocol_config import switch_protocol
    from simple_test_runner import SimpleProtocolTester
    from pathlib import Path
    
    print('⚙️  Switching to SWIM protocol...')
    switch_protocol('swim')
    
    print('🚀 Starting SWIM test...')
    tester = SimpleProtocolTester(Path('./output'))
    result = tester.run_swim_test(duration=60)
    print(f'✅ SWIM test completed! Results: {result}')
    
except Exception as e:
    print(f'❌ Error in SWIM test: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "📊 PHASE 3: ANALYSIS AND COMPARISON"
echo "==================================="

# Generate analysis
python3 -c "
import sys; sys.path.append('.')
try:
    from simple_analyzer import analyze_protocol_files
    from pathlib import Path
    import glob
    
    output_dir = Path('./output')
    hb_files = glob.glob('output/heartbeat_metrics_*.json')
    swim_files = glob.glob('output/swim_metrics_*.json')
    
    if hb_files and swim_files:
        latest_hb = max(hb_files)
        latest_swim = max(swim_files)
        print(f'📊 Analyzing: {latest_hb} vs {latest_swim}')
        analyze_protocol_files(latest_hb, latest_swim, output_dir)
        print('✅ Analysis completed!')
    else:
        print('❌ No metrics files found for analysis')
        
except Exception as e:
    print(f'❌ Error in analysis: {e}')
    import traceback
    traceback.print_exc()
"

# Generate graphs
echo "📈 Generating graphs..."
python3 graph_results.py

echo ""
echo "🎉 COMPARISON COMPLETE!"
echo "======================"
echo "📁 Results location: $(pwd)/output"
echo "📊 View graphs: open output/protocol_comparison_graphs.png"
echo "📋 Read report: cat output/detailed_comparison_analysis.md"
echo ""

# Show final results
echo "📄 QUICK SUMMARY:"
if [ -f "output/detailed_comparison_analysis.md" ]; then
    head -20 output/detailed_comparison_analysis.md
else
    echo "❌ Analysis report not found"
fi

# Open results
echo ""
echo "🔍 Opening results directory..."
open output 