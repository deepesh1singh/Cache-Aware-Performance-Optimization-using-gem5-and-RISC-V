#!/usr/bin/env python3
"""
Full Multi-Parameter Cache Sweep Script for gem5
This script performs a comprehensive sweep over multiple cache parameters.
"""

import os
import subprocess
import json
import argparse
import itertools
from pathlib import Path
from datetime import datetime


def run_simulation(gem5_bin, config_script, binary, l1i_size, l1d_size, l2_size, l1i_assoc, l1d_assoc, l2_assoc, output_dir):
    """Run a single gem5 simulation with specified parameters"""
    
    # Create output directory name based on parameters
    dir_name = f"l1i_{l1i_size}_l1d_{l1d_size}_l2_{l2_size}_assoc_{l1i_assoc}_{l1d_assoc}_{l2_assoc}"
    sim_output_dir = os.path.join(output_dir, dir_name)
    os.makedirs(sim_output_dir, exist_ok=True)
    
    # Build command
    cmd = [
        gem5_bin,
        f"--outdir={sim_output_dir}",
        config_script,
        f"--l1i_size={l1i_size}",
        f"--l1d_size={l1d_size}",
        f"--l2_size={l2_size}",
        f"--l1i_assoc={l1i_assoc}",
        f"--l1d_assoc={l1d_assoc}",
        f"--l2_assoc={l2_assoc}",
    ]
    
    if binary:
        cmd.append(f"--binary={binary}")
    
    print(f"Running: L1I={l1i_size}/{l1i_assoc}, L1D={l1d_size}/{l1d_assoc}, L2={l2_size}/{l2_assoc}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[:200]}")
            return None
        
        # Parse stats.txt
        stats_file = os.path.join(sim_output_dir, "stats.txt")
        stats = parse_stats(stats_file)
        stats['config'] = {
            'l1i_size': l1i_size,
            'l1d_size': l1d_size,
            'l2_size': l2_size,
            'l1i_assoc': l1i_assoc,
            'l1d_assoc': l1d_assoc,
            'l2_assoc': l2_assoc
        }
        
        print(f"Complete - Ticks: {stats.get('sim_ticks', 'N/A')}, L1D Hit Rate: {stats.get('l1d_hit_rate', 0):.2%}")
        return stats
        
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT")
        return None
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        return None


def parse_stats(stats_file):
    """Parse gem5 stats.txt file and extract key metrics"""
    stats = {}
    
    if not os.path.exists(stats_file):
        print(f"Stats file not found: {stats_file}")
        return stats
    
    with open(stats_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            
            parts = line.split()
            if len(parts) < 2:
                continue
            
            key = parts[0]
            value = parts[1]
            
            # Extract key metrics
            try:
                if key == 'simTicks':
                    stats['sim_ticks'] = int(value)
                elif key == 'simSeconds':
                    stats['sim_seconds'] = float(value)
                elif key == 'simInsts':
                    stats['sim_insts'] = int(value)
                elif key == 'system.cpu.cpi':
                    stats['cpi'] = float(value)
                elif key == 'system.cpu.ipc':
                    stats['ipc'] = float(value)
                elif key == 'system.cpu.dcache.overallHits::total':
                    stats['l1d_hits'] = int(value)
                elif key == 'system.cpu.dcache.overallMisses::total':
                    stats['l1d_misses'] = int(value)
                elif key == 'system.cpu.dcache.overallMissRate::total':
                    stats['l1d_miss_rate'] = float(value)
                elif key == 'system.cpu.icache.overallHits::total':
                    stats['l1i_hits'] = int(value)
                elif key == 'system.cpu.icache.overallMisses::total':
                    stats['l1i_misses'] = int(value)
                elif key == 'system.cpu.icache.overallMissRate::total':
                    stats['l1i_miss_rate'] = float(value)
                elif key == 'system.l2cache.overallHits::total':
                    stats['l2_hits'] = int(value)
                elif key == 'system.l2cache.overallMisses::total':
                    stats['l2_misses'] = int(value)
                elif key == 'system.l2cache.overallMissRate::total':
                    stats['l2_miss_rate'] = float(value)
                elif key == 'system.cpu.dcache.demandAvgMissLatency::total':
                    stats['l1d_avg_miss_latency'] = float(value)
                elif key == 'system.cpu.icache.demandAvgMissLatency::total':
                    stats['l1i_avg_miss_latency'] = float(value)
                elif key == 'system.l2cache.demandAvgMissLatency::total':
                    stats['l2_avg_miss_latency'] = float(value)
            except ValueError:
                continue
    
    # Calculate hit rates
    if 'l1d_hits' in stats and 'l1d_misses' in stats:
        total = stats['l1d_hits'] + stats['l1d_misses']
        stats['l1d_hit_rate'] = stats['l1d_hits'] / total if total > 0 else 0
    
    if 'l1i_hits' in stats and 'l1i_misses' in stats:
        total = stats['l1i_hits'] + stats['l1i_misses']
        stats['l1i_hit_rate'] = stats['l1i_hits'] / total if total > 0 else 0
    
    if 'l2_hits' in stats and 'l2_misses' in stats:
        total = stats['l2_hits'] + stats['l2_misses']
        stats['l2_hit_rate'] = stats['l2_hits'] / total if total > 0 else 0
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Full multi-parameter sweep for gem5 cache simulation')
    parser.add_argument('--gem5', required=True, help='Path to gem5 binary')
    parser.add_argument('--config', required=True, help='Path to cache_config.py')
    parser.add_argument('--binary', help='Path to workload binary (optional)')
    parser.add_argument('--output', default='full_sweep_results', help='Output directory')
    parser.add_argument('--quick', action='store_true', help='Run a quick subset of configurations')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Define parameter space
    if args.quick:
        # Quick sweep with fewer configurations
        l1i_sizes = ['16kB']
        l1d_sizes = ['16kB', '32kB', '64kB']
        l2_sizes = ['128kB', '256kB', '512kB']
        l1_assocs = [2, 4]
        l2_assocs = [4, 8]
    else:
        # Full sweep - matches problem statement requirements
        l1i_sizes = ['16kB']  # L1I kept constant as per problem statement
        l1d_sizes = ['16kB', '32kB', '64kB']
        l2_sizes = ['128kB', '256kB', '512kB', '1MB']
        l1_assocs = [2, 4, 8]
        l2_assocs = [4, 8, 16]
    
    # Generate all combinations
    configurations = list(itertools.product(l1i_sizes, l1d_sizes, l2_sizes, l1_assocs, l2_assocs))
    
    total = len(configurations)
    print(f"\n=== Full Cache Parameter Sweep ===")
    print(f"Total configurations: {total}")
    print(f"Output directory: {args.output}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    success_count = 0
    
    # Run all configurations
    for i, (l1i_size, l1d_size, l2_size, l1_assoc, l2_assoc) in enumerate(configurations, 1):
        print(f"\n[{i}/{total}] ", end="")
        
        stats = run_simulation(
            args.gem5, args.config, args.binary,
            l1i_size, l1d_size, l2_size,
            l1_assoc, l1_assoc, l2_assoc,  # Use same associativity for L1I and L1D
            args.output
        )
        
        if stats:
            results.append(stats)
            success_count += 1
    
    # Save results
    results_file = os.path.join(args.output, 'results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate summary
    summary = {
        'total_configurations': total,
        'successful_runs': success_count,
        'failed_runs': total - success_count,
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'l1i_sizes': l1i_sizes,
            'l1d_sizes': l1d_sizes,
            'l2_sizes': l2_sizes,
            'l1_assocs': l1_assocs,
            'l2_assocs': l2_assocs
        }
    }
    
    # Find best configurations
    if results:
        # Best by execution time
        best_time = min(results, key=lambda x: x.get('sim_ticks', float('inf')))
        summary['best_execution_time'] = {
            'config': best_time['config'],
            'sim_ticks': best_time.get('sim_ticks')
        }
        
        # Best by L1D hit rate
        best_l1d = max(results, key=lambda x: x.get('l1d_hit_rate', 0))
        summary['best_l1d_hit_rate'] = {
            'config': best_l1d['config'],
            'hit_rate': best_l1d.get('l1d_hit_rate')
        }
        
        # Best by L2 hit rate
        best_l2 = max(results, key=lambda x: x.get('l2_hit_rate', 0))
        summary['best_l2_hit_rate'] = {
            'config': best_l2['config'],
            'hit_rate': best_l2.get('l2_hit_rate')
        }
    
    summary_file = os.path.join(args.output, 'summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n\n=== Sweep Complete! ===")
    print(f"Successful runs: {success_count}/{total}")
    print(f"Results saved to: {results_file}")
    print(f"Summary saved to: {summary_file}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if results:
        print(f"\n=== Best Configurations ===")
        print(f"Fastest execution: {best_time['config']} ({best_time.get('sim_ticks')} ticks)")
        print(f"Best L1D hit rate: {best_l1d['config']} ({best_l1d.get('l1d_hit_rate', 0):.2%})")
        print(f"Best L2 hit rate: {best_l2['config']} ({best_l2.get('l2_hit_rate', 0):.2%})")


if __name__ == '__main__':
    main()
