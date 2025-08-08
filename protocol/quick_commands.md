# 🚀 Protocol Comparison Commands (100 Devices)

## 🎯 **ONE-COMMAND SOLUTION (RECOMMENDED)**
```bash
./run_full_comparison.sh
```

---

## 📋 **INDIVIDUAL COMMANDS (Manual Step-by-Step)**

### **1. Setup Environment**
```bash
cd /Users/bnjoroge/Documents/leader_follower/protocol
export PYTHONPATH=$PYTHONPATH:$(pwd)
source .venv/bin/activate
pip install matplotlib seaborn pandas numpy psutil
```

### **2. Clean Previous Results**
```bash
rm -f output/heartbeat_metrics_*.json output/swim_metrics_*.json output/*comparison*.md output/*.png
```

### **3. Run Heartbeat Test (100 devices, 60 seconds)**
```bash
# Switch to heartbeat protocol
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; switch_protocol('heartbeat')"

# Run test
python3 -c "
import sys; sys.path.append('.')
from simple_test_runner import SimpleProtocolTester
from pathlib import Path
tester = SimpleProtocolTester(Path('./output'))
print('🔥 Starting Heartbeat Test with 100 devices for 60 seconds...')
result = tester.run_heartbeat_test(duration=60, num_devices=100)
print(f'✅ Heartbeat test completed! File: {result}')
"
```

### **4. Run SWIM Test (100 devices, 60 seconds)**
```bash
# Switch to SWIM protocol
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; switch_protocol('swim')"

# Run test
python3 -c "
import sys; sys.path.append('.')
from simple_test_runner import SimpleProtocolTester
from pathlib import Path
tester = SimpleProtocolTester(Path('./output'))
print('🏊 Starting SWIM Test with 100 devices for 60 seconds...')
result = tester.run_swim_test(duration=60, num_devices=100)
print(f'✅ SWIM test completed! File: {result}')
"
```

### **5. Generate Analysis and Graphs**
```bash
# Run comparison analysis
python3 -c "
import sys; sys.path.append('.')
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
    print('❌ No metrics files found')
"

# Generate visual graphs
python3 graph_results.py
```

### **6. View Results**
```bash
# Open results directory
open output

# View text analysis
cat output/detailed_comparison_analysis.md

# View visual graphs (if matplotlib worked)
open output/protocol_comparison_graphs.png
```

---

## 🔧 **QUICK CONFIGURATION COMMANDS**

### **Switch Protocol Only**
```bash
# Switch to Heartbeat
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; switch_protocol('heartbeat')"

# Switch to SWIM
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; switch_protocol('swim')"

# Check current protocol
python3 -c "import sys; sys.path.append('.'); from protocol_config import get_current_protocol; print(f'Current protocol: {get_current_protocol()}')"
```

### **Quick Test (10 devices, 30 seconds)**
```bash
# Heartbeat quick test
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; from simple_test_runner import SimpleProtocolTester; from pathlib import Path; switch_protocol('heartbeat'); tester = SimpleProtocolTester(Path('./output')); result = tester.run_heartbeat_test(duration=30, num_devices=10); print(f'Quick heartbeat test: {result}')"

# SWIM quick test  
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; from simple_test_runner import SimpleProtocolTester; from pathlib import Path; switch_protocol('swim'); tester = SimpleProtocolTester(Path('./output')); result = tester.run_swim_test(duration=30, num_devices=10); print(f'Quick SWIM test: {result}')"
```

---

## 📊 **EXPECTED RESULTS LOCATION**
- **📁 Directory**: `./output/`
- **📈 Graphs**: `protocol_comparison_graphs.png`  
- **📋 Analysis**: `detailed_comparison_analysis.md`
- **📊 Raw Data**: `heartbeat_metrics_*.json`, `swim_metrics_*.json` 