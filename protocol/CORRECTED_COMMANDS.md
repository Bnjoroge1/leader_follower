# 🚀 CORRECTED Protocol Comparison Commands (100 Devices)

## ⚠️ **CRITICAL: MUST RUN FROM PROTOCOL DIRECTORY**

```bash
# STEP 0: Navigate to the correct directory FIRST!
cd /Users/bnjoroge/Documents/leader_follower/protocol
```

**❌ DO NOT run from `/protocol/output` or any subdirectory**  
**✅ MUST run from `/protocol` (main directory)**

---

## 🎯 **ONE-COMMAND SOLUTION (EASIEST)**

```bash
# Make sure you're in the protocol directory first!
cd /Users/bnjoroge/Documents/leader_follower/protocol
./run_full_comparison.sh
```

---

## 📋 **STEP-BY-STEP COMMANDS (Copy-Paste Ready)**

### **1. Setup Environment (Run Once)**
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

### **3. Run Heartbeat Test (60 seconds)**
```bash
# Switch to heartbeat protocol
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; switch_protocol('heartbeat'); print('✅ Switched to heartbeat')"

# Run heartbeat test
python3 -c "
import sys; sys.path.append('.')
from simple_test_runner import SimpleProtocolTester
from pathlib import Path
tester = SimpleProtocolTester(Path('./output'))
print('🔥 Starting Heartbeat Test for 60 seconds...')
result = tester.run_heartbeat_test(duration=60)
print(f'✅ Heartbeat test completed! File: {result}')
"
```

### **4. Run SWIM Test (60 seconds)**
```bash
# Switch to SWIM protocol
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; switch_protocol('swim'); print('✅ Switched to SWIM')"

# Run SWIM test
python3 -c "
import sys; sys.path.append('.')
from simple_test_runner import SimpleProtocolTester
from pathlib import Path
tester = SimpleProtocolTester(Path('./output'))
print('🏊 Starting SWIM Test for 60 seconds...')
result = tester.run_swim_test(duration=60)
print(f'✅ SWIM test completed! File: {result}')
"
```

### **5. Generate Analysis and Graphs**
```bash
# Generate comparison analysis
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
    print('❌ No metrics files found for analysis')
"

# Generate visual graphs
python3 graph_results.py
```

### **6. View Results**
```bash
# Open results directory
open output

# View analysis report
cat output/detailed_comparison_analysis.md

# View graphs (if matplotlib worked)
open output/protocol_comparison_graphs.png
```

---

## 🔧 **QUICK UTILITY COMMANDS**

### **Check Current Directory (Run This First!)**
```bash
pwd
# Should show: /Users/bnjoroge/Documents/leader_follower/protocol
# If not, run: cd /Users/bnjoroge/Documents/leader_follower/protocol
```

### **Switch Protocol Only**
```bash
# Switch to Heartbeat
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; switch_protocol('heartbeat')"

# Switch to SWIM  
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; switch_protocol('swim')"

# Check current protocol
python3 -c "import sys; sys.path.append('.'); from protocol_config import get_current_protocol; print(f'Current protocol: {get_current_protocol()}')"
```

### **Quick Test (30 seconds)**
```bash
# Quick heartbeat test
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; from simple_test_runner import SimpleProtocolTester; from pathlib import Path; switch_protocol('heartbeat'); tester = SimpleProtocolTester(Path('./output')); result = tester.run_heartbeat_test(duration=30); print(f'Quick heartbeat: {result}')"

# Quick SWIM test
python3 -c "import sys; sys.path.append('.'); from protocol_config import switch_protocol; from simple_test_runner import SimpleProtocolTester; from pathlib import Path; switch_protocol('swim'); tester = SimpleProtocolTester(Path('./output')); result = tester.run_swim_test(duration=30); print(f'Quick SWIM: {result}')"
```

---

## 📊 **RESULTS LOCATION**
- **📁 Directory**: `./output/` (relative to protocol directory)
- **📈 Graphs**: `output/protocol_comparison_graphs.png`
- **📋 Analysis**: `output/detailed_comparison_analysis.md`  
- **📊 Raw Data**: `output/heartbeat_metrics_*.json`, `output/swim_metrics_*.json`

---

## ⚠️ **TROUBLESHOOTING**

**Error: `ModuleNotFoundError: No module named 'protocol_config'`**
- **Solution**: Make sure you're in `/Users/bnjoroge/Documents/leader_follower/protocol` directory
- **Check**: Run `pwd` - should show the protocol directory path
- **Fix**: Run `cd /Users/bnjoroge/Documents/leader_follower/protocol`

**Error: `ModuleNotFoundError: No module named 'simple_test_runner'`**  
- **Solution**: Same as above - wrong directory
- **Fix**: Navigate to protocol directory first 