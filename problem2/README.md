# Problem 2: MergeSort Cache Analysis

## Overview
This assignment analyzes cache performance differences between two merge sort implementations (simple and chunked) on a 10MB dataset using gem5 simulation.

## Directory Structure
```
problem2/
├── scripts/                          # Python scripts
│   ├── simple-riscv_mergesort_simple.py    # Simple mergesort config
│   ├── simple-riscv_mergesort_chunked.py   # Chunked mergesort config
│   ├── sweep_mergesort.py                   # Parameter sweep script
│   ├── analyze_results.py                   # Analysis script
│   └── reparse_stats.py                     # Stats re-parsing utility
├── output/                           # Individual simulation outputs
├── sweep_result/                     # Sweep results (generated)
├── analysis/                         # Analysis outputs (generated)
├── random_numbers.bin                # test data
└── README.md
```

**NOTE:** This code is for ARM.

## Installation
```bash
# Install Python dependencies
pip install pandas matplotlib seaborn numpy

# Verify RISC-V compiler
riscv64-linux-gnu-gcc --version
```

## Step 1: Compile Binaries

```bash
cd problem2/scripts

# Compile simple mergesort
riscv64-linux-gnu-gcc -static -o mergesort_s mergesort_simple.c \
    -march=rv64imafdc -mabi=lp64d -O2

# Compile chunked mergesort
riscv64-linux-gnu-gcc -static -o mergesort_c mergesort_chunked.c \
    -march=rv64imafdc -mabi=lp64d -O2
```

## Step 2: Run Baseline Simulations

### Simple MergeSort (Baseline)
```bash
cd ../gem5

./build/RISCV/gem5.opt \
    --outdir=../problem2/output/simple_baseline \
    ../problem2/scripts/simple-riscv_mergesort_simple.py \
    --l1i_size=32KiB \
    --l1d_size=64KiB \
    --l2_size=512KiB \
    --l1_assoc=8 \
    --l2_assoc=16
```

### Chunked MergeSort (Baseline)
```bash
./build/RISCV/gem5.opt \
    --outdir=../problem2/output/chunked_baseline \
    ../problem2/scripts/simple-riscv_mergesort_chunked.py \
    --l1i_size=32KiB \
    --l1d_size=64KiB \
    --l2_size=512KiB \
    --l1_assoc=8 \
    --l2_assoc=16
```

**Default Configuration:**
- L1I: 32KiB, 8-way
- L1D: 64KiB, 8-way
- L2: 512KiB, 16-way

## Step 3: Run Parameter Sweep

```bash
cd ../problem2

python3 scripts/sweep_mergesort.py \
    --gem5 ../gem5/build/RISCV/gem5.opt \
    --output sweep_result \
    --variants simple \
    --parallel 6
```
**Note:** Rename results.json to results_simple.json in sweep_results

```bash
python3 scripts/sweep_mergesort.py \
    --gem5 ../gem5/build/RISCV/gem5.opt \
    --output sweep_result \
    --variants chunked \
    --parallel 6
```
**Note:** Rename results.json to results_chunked.json in sweep_results

**Sweep Parameters:**
- L1D sizes: 32KiB, 64KiB, 128KiB
- L2 sizes: 256KiB, 512KiB, 1MB
- L1 associativity: 4, 8, 16
- L2 associativity: 4, 8, 16

**Note:** Full sweep runs 81 configurations per variant (~162 total simulations)

## Step 4: Analyze Results

### Option A: If you already have stats files but need to update JSON
```bash
python3 scripts/reparse_stats.py --sweep-dir sweep_result
```

### Generate Analysis Report
```bash
python3 scripts/analyze_results.py \
    --simple sweep_result/results_simple.json \
    --chunked sweep_result/results_chunked.json \
    --output analysis
```

**Generated Files:**

**Part 1 (Baseline Comparison):**
- `part1_baseline_comparison.csv` - Side-by-side stats comparison
- `part1_baseline_comparison.txt` - Formatted text version

**Part 2 (Sweep Results):**
- `part2_full_results.csv` - Complete sweep results
- `part2_top3_simple.csv` - Top 3 configs for simple mergesort
- `part2_top3_chunked.csv` - Top 3 configs for chunked mergesort
- `part2_top_configs.txt` - Formatted top configurations

**Plots:**
- `plot1_l2_miss_rate_vs_l2_size.png`
- `plot2_ipc_vs_l1d_size.png`
- `plot3_l1d_hit_rate_vs_associativity.png`
- `plot4_simple_vs_chunked_comparison.png`
- `plot5_simple_ipc_heatmap.png`
- `plot6_chunked_ipc_heatmap.png`

**Summary:**
- `ANALYSIS_SUMMARY.txt` - Complete deliverables summary

