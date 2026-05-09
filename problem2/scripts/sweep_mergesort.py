#!/usr/bin/env python3
"""
Parameter sweep script for merge sort simulations.
Runs both simple and chunked merge sort with different cache configurations.
Supports parallel execution for faster sweeps.
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from itertools import product
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

def run_simulation(config):
    """Run a single simulation with given configuration."""
    gem5_bin = config['gem5_bin']
    script = config['script']
    l1i_size = config['l1i_size']
    l1d_size = config['l1d_size']
    l2_size = config['l2_size']
    l1_assoc = config['l1_assoc']
    l2_assoc = config['l2_assoc']
    output_dir = config['output_dir']
    variant = config['variant']
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Build command
    cmd = [
        gem5_bin,
        f'--outdir={output_dir}',
        script,
        f'--l1i_size={l1i_size}',
        f'--l1d_size={l1d_size}',
        f'--l2_size={l2_size}',
        f'--l1_assoc={l1_assoc}',
        f'--l2_assoc={l2_assoc}'
    ]
    
    config_str = f"{variant}: L1I={l1i_size}, L1D={l1d_size}, L2={l2_size}, L1_assoc={l1_assoc}, L2_assoc={l2_assoc}"
    
    try:
        print(f"[START] {config_str}")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            print(f"[FAILED] {config_str}")
            print(f"  Error: {result.stderr[:200]}")
            return {
                'config': config,
                'success': False,
                'error': result.stderr,
                'elapsed_time': elapsed
            }
        
        # Parse stats from output
        stats_file = Path(output_dir) / 'stats.txt'
        stats = parse_stats(stats_file)
        
        print(f"[DONE] {config_str} (took {elapsed:.1f}s)")
        
        return {
            'config': {
                'variant': variant,
                'l1i_size': l1i_size,
                'l1d_size': l1d_size,
                'l2_size': l2_size,
                'l1_assoc': l1_assoc,
                'l2_assoc': l2_assoc
            },
            'stats': stats,
            'success': True,
            'elapsed_time': elapsed,
            'output_dir': output_dir
        }
        
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {config_str}")
        return {
            'config': config,
            'success': False,
            'error': 'Simulation timeout (>1 hour)',
            'elapsed_time': 3600
        }
    except Exception as e:
        print(f"[ERROR] {config_str}: {str(e)}")
        return {
            'config': config,
            'success': False,
            'error': str(e),
            'elapsed_time': 0
        }


def parse_stats(stats_file):
    """Parse key statistics from gem5 stats.txt file."""
    stats = {}
    
    if not os.path.exists(stats_file):
        return stats
    
    with open(stats_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            
            # Parse stat lines (format: "stat_name   value   # description")
            parts = line.split()
            if len(parts) >= 2:
                stat_name = parts[0]
                stat_value = parts[1]
                
                # Extract key statistics
                if stat_name == 'simSeconds':
                    stats['sim_seconds'] = float(stat_value)
                elif stat_name == 'simTicks':
                    stats['sim_ticks'] = int(stat_value)
                elif stat_name == 'simInsts':
                    stats['sim_insts'] = int(stat_value)
                elif stat_name == 'system.cpu.cpi':
                    stats['cpi'] = float(stat_value)
                elif stat_name == 'system.cpu.ipc':
                    stats['ipc'] = float(stat_value)
                elif stat_name == 'system.cpu.numCycles':
                    stats['num_cycles'] = int(stat_value)
                elif stat_name == 'system.cpu.dcache.demandMisses::total':
                    stats['l1d_misses'] = int(stat_value)
                elif stat_name == 'system.cpu.dcache.demandHits::total':
                    stats['l1d_hits'] = int(stat_value)
                elif stat_name == 'system.cpu.dcache.demandAccesses::total':
                    stats['l1d_accesses'] = int(stat_value)
                elif stat_name == 'system.cpu.icache.demandMisses::total':
                    stats['l1i_misses'] = int(stat_value)
                elif stat_name == 'system.cpu.icache.demandHits::total':
                    stats['l1i_hits'] = int(stat_value)
                elif stat_name == 'system.cpu.icache.demandAccesses::total':
                    stats['l1i_accesses'] = int(stat_value)
                elif stat_name == 'system.l2cache.demandMisses::total':
                    stats['l2_misses'] = int(stat_value)
                elif stat_name == 'system.l2cache.demandHits::total':
                    stats['l2_hits'] = int(stat_value)
                elif stat_name == 'system.l2cache.demandAccesses::total':
                    stats['l2_accesses'] = int(stat_value)
                elif stat_name == 'system.cpu.dcache.overallMissRate::total':
                    stats['l1d_miss_rate'] = float(stat_value)
                elif stat_name == 'system.cpu.icache.overallMissRate::total':
                    stats['l1i_miss_rate'] = float(stat_value)
                elif stat_name == 'system.l2cache.overallMissRate::total':
                    stats['l2_miss_rate'] = float(stat_value)
    
    # Calculate hit rates if we have hits and misses
    if 'l1d_hits' in stats and 'l1d_misses' in stats:
        total = stats['l1d_hits'] + stats['l1d_misses']
        if total > 0:
            stats['l1d_hit_rate'] = stats['l1d_hits'] / total
    
    if 'l1i_hits' in stats and 'l1i_misses' in stats:
        total = stats['l1i_hits'] + stats['l1i_misses']
        if total > 0:
            stats['l1i_hit_rate'] = stats['l1i_hits'] / total
    
    if 'l2_hits' in stats and 'l2_misses' in stats:
        total = stats['l2_hits'] + stats['l2_misses']
        if total > 0:
            stats['l2_hit_rate'] = stats['l2_hits'] / total
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Run parameter sweep for merge sort simulations')
    parser.add_argument('--gem5', type=str, required=True, help='Path to gem5 binary')
    parser.add_argument('--output', type=str, default='sweep_results', help='Output directory for results')
    parser.add_argument('--simple-script', type=str, 
                       default='scripts/simple-riscv_mergesort_simple.py',
                       help='Path to simple merge sort script')
    parser.add_argument('--chunked-script', type=str,
                       default='scripts/simple-riscv_mergesort_chunked.py', 
                       help='Path to chunked merge sort script')
    parser.add_argument('--variants', type=str, nargs='+', 
                       default=['simple', 'chunked'],
                       choices=['simple', 'chunked'],
                       help='Which variants to run')
    parser.add_argument('--parallel', type=int, default=1,
                       help='Number of parallel processes (1=sequential)')
    
    # Cache parameter ranges
    parser.add_argument('--l1-sizes', type=str, nargs='+',
                       default=['32KiB', '64KiB', '128KiB'],
                       help='L1 cache sizes to test')
    parser.add_argument('--l2-sizes', type=str, nargs='+',
                       default=['256KiB', '512KiB', '1MB'],
                       help='L2 cache sizes to test')
    parser.add_argument('--l1-assoc', type=int, nargs='+',
                       default=[4, 8, 16],
                       help='L1 associativity values to test')
    parser.add_argument('--l2-assoc', type=int, nargs='+',
                       default=[4, 8, 16],
                       help='L2 associativity values to test')
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute
    gem5_bin = os.path.abspath(args.gem5)
    output_base = os.path.abspath(args.output)
    simple_script = os.path.abspath(args.simple_script)
    chunked_script = os.path.abspath(args.chunked_script)
    
    # Verify files exist
    if not os.path.exists(gem5_bin):
        print(f"Error: gem5 binary not found: {gem5_bin}")
        return 1
    
    if 'simple' in args.variants and not os.path.exists(simple_script):
        print(f"Error: Simple script not found: {simple_script}")
        return 1
    
    if 'chunked' in args.variants and not os.path.exists(chunked_script):
        print(f"Error: Chunked script not found: {chunked_script}")
        return 1
    
    # Generate all configurations
    configs = []
    
    for variant in args.variants:
        script = simple_script if variant == 'simple' else chunked_script
        
        # L1I is typically kept at 32KiB (instruction cache)
        l1i_size = '32KiB'
        
        for l1d_size, l2_size, l1_assoc, l2_assoc in product(
            args.l1_sizes, args.l2_sizes, args.l1_assoc, args.l2_assoc
        ):
            config_name = f"{variant}_L1D{l1d_size}_L2{l2_size}_L1A{l1_assoc}_L2A{l2_assoc}"
            output_dir = os.path.join(output_base, config_name)
            
            configs.append({
                'gem5_bin': gem5_bin,
                'script': script,
                'variant': variant,
                'l1i_size': l1i_size,
                'l1d_size': l1d_size,
                'l2_size': l2_size,
                'l1_assoc': l1_assoc,
                'l2_assoc': l2_assoc,
                'output_dir': output_dir
            })
    
    print(f"MERGE SORT CACHE PARAMETER SWEEP")
    print(f"Total configurations: {len(configs)}")
    print(f"Variants: {args.variants}")
    print(f"L1D sizes: {args.l1_sizes}")
    print(f"L2 sizes: {args.l2_sizes}")
    print(f"L1 associativity: {args.l1_assoc}")
    print(f"L2 associativity: {args.l2_assoc}")
    print(f"Parallel processes: {args.parallel}")
    print(f"Output directory: {output_base}")
    print()
    
    # Run simulations
    results = []
    start_time = time.time()
    
    if args.parallel > 1:
        print(f"Running {len(configs)} simulations in parallel with {args.parallel} workers...\n")
        with ProcessPoolExecutor(max_workers=args.parallel) as executor:
            futures = {executor.submit(run_simulation, config): config for config in configs}
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
    else:
        print(f"Running {len(configs)} simulations sequentially...\n")
        for i, config in enumerate(configs, 1):
            print(f"[{i}/{len(configs)}]", end=' ')
            result = run_simulation(config)
            results.append(result)
    
    total_time = time.time() - start_time
    
    # Save results
    results_file = os.path.join(output_base, 'results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print("SWEEP COMPLETE")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(f"Results saved to: {results_file}")
    
    # Show top 3 by IPC for each variant
    for variant in args.variants:
        variant_results = [r for r in results if r['success'] and r['config']['variant'] == variant]
        variant_results.sort(key=lambda x: x['stats'].get('ipc', 0), reverse=True)
        
        print(f"\nTop 3 configurations for {variant.upper()} (by IPC):")
        for i, result in enumerate(variant_results[:3], 1):
            cfg = result['config']
            stats = result['stats']
            print(f"  {i}. L1D={cfg['l1d_size']}, L2={cfg['l2_size']}, "
                  f"L1_assoc={cfg['l1_assoc']}, L2_assoc={cfg['l2_assoc']}")
            print(f"     IPC: {stats.get('ipc', 0):.4f}, "
                  f"CPI: {stats.get('cpi', 0):.4f}, "
                  f"Sim time: {stats.get('sim_seconds', 0):.4f}s")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
