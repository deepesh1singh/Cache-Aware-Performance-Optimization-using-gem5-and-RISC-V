#!/usr/bin/env python3
"""
Custom Parameter Sweep Script for gem5 Cache Configuration
This script performs a sweep over a single cache parameter while keeping others constant.
"""

import os
import subprocess
import json
import argparse
from pathlib import Path


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
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"Error running simulation: {result.stderr}")
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
        return stats
        
    except subprocess.TimeoutExpired:
        print(f"Simulation timed out")
        return None
    except Exception as e:
        print(f"Exception during simulation: {e}")
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
            if key == 'simTicks':
                stats['sim_ticks'] = int(value)
            elif key == 'simSeconds':
                stats['sim_seconds'] = float(value)
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
    parser = argparse.ArgumentParser(description='Custom single-parameter sweep for gem5 cache simulation')
    parser.add_argument('--gem5', required=True, help='Path to gem5 binary')
    parser.add_argument('--config', required=True, help='Path to cache_config.py')
    parser.add_argument('--binary', help='Path to workload binary (optional)')
    parser.add_argument('--output', default='single_param_sweep', help='Output directory')
    parser.add_argument('--param', choices=['l1d_size', 'l2_size', 'l1_assoc', 'l2_assoc'], 
                        default='l1d_size', help='Parameter to sweep')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Define default configuration (matches problem statement Part 2)
    default_config = {
        'l1i_size': '16kB',  # L1I kept constant
        'l1d_size': '16kB',
        'l2_size': '256kB',
        'l1i_assoc': 4,  # L1I assoc kept constant
        'l1d_assoc': 4,
        'l2_assoc': 8
    }
    
    # Define sweep values for each parameter (per problem statement)
    sweep_configs = {
        'l1d_size': ['16kB', '32kB', '64kB'],
        'l2_size': ['128kB', '256kB', '512kB', '1MB'],
        'l1_assoc': [2, 4, 8],
        'l2_assoc': [4, 8, 16]
    }
    
    results = []
    
    print(f"\n=== Starting sweep for parameter: {args.param} ===\n")
    
    # Perform sweep
    if args.param == 'l1d_size':
        for size in sweep_configs['l1d_size']:
            config = default_config.copy()
            config['l1d_size'] = size
            print(f"\nTesting L1D size: {size}")
            stats = run_simulation(
                args.gem5, args.config, args.binary,
                config['l1i_size'], config['l1d_size'], config['l2_size'],
                config['l1i_assoc'], config['l1d_assoc'], config['l2_assoc'],
                args.output
            )
            if stats:
                results.append(stats)
    
    elif args.param == 'l2_size':
        for size in sweep_configs['l2_size']:
            config = default_config.copy()
            config['l2_size'] = size
            print(f"\nTesting L2 size: {size}")
            stats = run_simulation(
                args.gem5, args.config, args.binary,
                config['l1i_size'], config['l1d_size'], config['l2_size'],
                config['l1i_assoc'], config['l1d_assoc'], config['l2_assoc'],
                args.output
            )
            if stats:
                results.append(stats)
    
    elif args.param == 'l1_assoc':
        for assoc in sweep_configs['l1_assoc']:
            config = default_config.copy()
            config['l1d_assoc'] = assoc
            config['l1i_assoc'] = assoc
            print(f"\nTesting L1 associativity: {assoc}")
            stats = run_simulation(
                args.gem5, args.config, args.binary,
                config['l1i_size'], config['l1d_size'], config['l2_size'],
                config['l1i_assoc'], config['l1d_assoc'], config['l2_assoc'],
                args.output
            )
            if stats:
                results.append(stats)
    
    elif args.param == 'l2_assoc':
        for assoc in sweep_configs['l2_assoc']:
            config = default_config.copy()
            config['l2_assoc'] = assoc
            print(f"\nTesting L2 associativity: {assoc}")
            stats = run_simulation(
                args.gem5, args.config, args.binary,
                config['l1i_size'], config['l1d_size'], config['l2_size'],
                config['l1i_assoc'], config['l1d_assoc'], config['l2_assoc'],
                args.output
            )
            if stats:
                results.append(stats)
    
    # Save results
    results_file = os.path.join(args.output, 'results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Sweep complete! ===")
    print(f"Results saved to: {results_file}")
    print(f"Total simulations: {len(results)}")


if __name__ == '__main__':
    main()
