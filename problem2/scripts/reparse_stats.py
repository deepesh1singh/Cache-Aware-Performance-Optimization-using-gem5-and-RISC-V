#!/usr/bin/env python3
"""
Re-parse existing stats.txt files and update JSON results files.
This script reads all stats.txt files from the sweep results and regenerates
the JSON files with complete statistics.
"""

import json
import os
from pathlib import Path
import argparse


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


def parse_config_from_dirname(dirname):
    """Parse configuration from directory name.
    Format: {variant}_L1D{size}_L2{size}_L1A{assoc}_L2A{assoc}
    """
    parts = dirname.split('_')
    config = {
        'variant': parts[0],
        'l1i_size': '32KiB', 
    }
    
    for part in parts[1:]:
        if part.startswith('L1D'):
            config['l1d_size'] = part[3:]
        elif part.startswith('L2') and not part.startswith('L2A'):
            config['l2_size'] = part[2:]
        elif part.startswith('L1A'):
            config['l1_assoc'] = int(part[3:])
        elif part.startswith('L2A'):
            config['l2_assoc'] = int(part[3:])
    
    return config


def reparse_sweep_results(sweep_dir):
    """Re-parse all stats files in the sweep directory."""
    sweep_path = Path(sweep_dir)
    
    simple_results = []
    chunked_results = []
    
    # Find all stats.txt files
    stats_files = list(sweep_path.glob('*/stats.txt'))
    
    print(f"Found {len(stats_files)} stats files to parse...")
    
    for stats_file in stats_files:
        dirname = stats_file.parent.name
        
        # Parse configuration from directory name
        config = parse_config_from_dirname(dirname)
        
        # Parse stats
        stats = parse_stats(stats_file)
        
        if not stats:
            print(f"Warning: Could not parse stats from {stats_file}")
            continue
        
        result = {
            'config': config,
            'stats': stats,
            'success': True
        }
        
        if config['variant'] == 'simple':
            simple_results.append(result)
        elif config['variant'] == 'chunked':
            chunked_results.append(result)
    
    print(f"Parsed {len(simple_results)} simple configurations")
    print(f"Parsed {len(chunked_results)} chunked configurations")
    
    return simple_results, chunked_results


def main():
    parser = argparse.ArgumentParser(description='Re-parse stats files and update JSON results')
    parser.add_argument('--sweep-dir', type=str, default='sweep_result',
                        help='Directory containing sweep results')
    parser.add_argument('--output-dir', type=str, default='sweep_result',
                        help='Directory to save updated JSON files')
    args = parser.parse_args()
    
    print("RE-PARSING SWEEP RESULTS")
    print(f"Sweep directory: {args.sweep_dir}")
    print()
    
    # Re-parse all results
    simple_results, chunked_results = reparse_sweep_results(args.sweep_dir)
    
    # Save updated JSON files
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)
    
    simple_json = output_path / 'results_simple.json'
    chunked_json = output_path / 'results_chunked.json'
    
    with open(simple_json, 'w') as f:
        json.dump(simple_results, f, indent=2)
    print(f"Saved updated simple results: {simple_json}")
    
    with open(chunked_json, 'w') as f:
        json.dump(chunked_results, f, indent=2)
    print(f"Saved updated chunked results: {chunked_json}")
    
    print()
    print("RE-PARSING COMPLETE!")
    print()
    print("Next step: Run the analysis script again to regenerate tables and plots:")
    print("  python3 scripts/analyze_results.py")
    print()


if __name__ == '__main__':
    main()
