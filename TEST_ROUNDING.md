# Testing Rounding Direction Analysis

## Quick Test Commands

### Analyze all functions in a contract:
```bash
cd /Volumes/Trail/slither
PYTHONPATH=/Volumes/Trail/slither python3 slither/analyses/data_flow/analyses/rounding/test_rounding.py ../contracts/src/Rounding.sol
```

### Analyze a specific function:
```bash
cd /Volumes/Trail/slither
PYTHONPATH=/Volumes/Trail/slither python3 slither/analyses/data_flow/analyses/rounding/test_rounding.py ../contracts/src/Rounding.sol swapBtoA_Vulnerable
```

### Run the detector (find violations):
```bash
cd /Volumes/Trail/slither
python3 -m slither --detect rounding ../contracts/src/Rounding.sol
```

## What Each Tool Does

1. **test_rounding.py** - Visualization tool showing all variables and their rounding tags
   - Shows detailed breakdown per function
   - Displays variable flow through operations
   - Summary table of all functions

2. **--detect rounding** - Detector that finds violations
   - Flags mismatches between function names and implementation
   - Reports errors/warnings

## Example Output

The visualization shows:
- 🔼 UP - Variable rounds up
- 🔽 DOWN - Variable rounds down  
- ❓ UNKNOWN - Rounding direction unclear

Each function shows:
- Variables and their tags at each node
- Operations that create variables
- Return value tags
- Expected vs actual comparison
