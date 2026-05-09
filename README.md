# Problem 1: Cache Parameter Sweep

## Overview
This assignment performs a comprehensive cache parameter sweep using gem5 to analyze the impact of L1 and L2 cache configurations on benchmark performance.

## Directory Structure
```
problem1/
├── benchmarks/        # Benchmark binaries
│   ├── matrix_multiply.c   # benchmark program
├── configs/          # gem5 configuration script
│   ├── cache_config.py    # config script 
├── scripts/          # Sweep and analysis scripts
│   ├── custom_sweep.py    # sweep of single param
│   ├── full_sweep.py   # full sweep of all param combinations
│   ├── analyze_sweep.py    # analysis of results
├── results/          # Simulation results (generated)
└── README.md
```

**NOTE:** This code is for ARM.

## Installation
```bash
# Install required Python packages
pip install pandas matplotlib numpy seaborn
```

## Running Simulations

### Option 1: Run Single Configuration (Direct Config File)
To run a single simulation with specific cache parameters:

```bash
cd gem5

# Run with default config parameters (defined in cache_config.py)
./build/RISCV/gem5.opt \
    --outdir=../problem1/output/default \
    ../problem1/configs/cache_config.py

# Run with custom parameters
./build/RISCV/gem5.opt \
    --outdir=../problem1/output/custom \
    ../problem1/configs/cache_config.py \
    --l1i_size=32kB \
    --l1d_size=64kB \
    --l2_size=512kB \
    --l1i_assoc=4 \
    --l1d_assoc=4 \
    --l2_assoc=8 \
    --binary=/path/to/your/benchmark
```

**Config file parameters:**
- `--l1i_size`, `--l1d_size`, `--l2_size` (e.g., 16kB, 32kB, 64kB)
- `--l1i_assoc`, `--l1d_assoc`, `--l2_assoc` (e.g., 2, 4, 8)
- `--binary` (path to RISC-V benchmark binary)

### Option 2: Full Multi-Parameter Sweep
Run a comprehensive sweep over all cache parameters using the sweep script:

```bash
cd problem1
python3 scripts/cache_sweep.py \
    --gem5 ../gem5/build/RISCV/gem5.opt \
    --config configs/cache_config.py \
    --binary benchmarks/matrix_multiply \
    --output results/full_sweep
```

**Parameters swept:**
- L1I size: 16kB
- L1D sizes: 16kB, 32kB, 64kB
- L2 sizes: 256kB, 512kB, 1024kB
- L1 associativity: 2, 4, 8
- L2 associativity: 4, 8, 16

### Option 3: Single Parameter Sweep
Run a focused sweep varying one parameter while keeping others constant:

```bash
python3 scripts/custom_sweep.py \
    --gem5 ../gem5/build/RISCV/gem5.opt \
    --config configs/cache_config.py \
    --binary benchmarks/matrix_multiply \
    --output results/custom_sweep \
    --param l1d_size 
```

**Available parameters:**
- `l1d_size`, `l2_size`, `l1_assoc`, `l2_assoc`

## Analyzing Results

### Generate Analysis Report
```bash
python3 scripts/analyze_sweep.py \
    --results results/full_sweep/results.json \
    --output results/analysis
```

**Generated outputs:**
- `full_results_table.csv` - Complete results table with all configurations
- `summary_statistics.csv` - Statistical summary (mean, min, max, std)
- `top3_execution_time.csv` - Top 3 configs by lowest execution time
- `top3_l1d_hit_rate.csv` - Top 3 configs by highest L1D hit rate
- `top3_l2_hit_rate.csv` - Top 3 configs by highest L2 hit rate
- `pareto_optimal_configs.csv` - Pareto-optimal configurations
- `design_recommendations.csv` - Design recommendations
- `plots:
  - `l1d_size_impact.png` - Performance vs L1D size
  - `l2_size_impact.png` - Performance vs L2 size
  - `associativity_impact.png` - Impact of associativity
  - `performance_heatmap.png` - Configuration heatmap
  - `pareto_frontier.png` - Pareto frontier visualization

## Output Files

Each simulation creates a directory with:
- `stats.txt` - gem5 statistics file
- `config.ini` - Configuration snapshot
- `config.json` - Configuration metadata

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
