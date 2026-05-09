#!/usr/bin/env python3
"""
Analysis script for Problem 2: MergeSort Cache Analysis
Generates tables and plots for both Part 1 (baseline) and Part 2 (sweep) requirements.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import argparse

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

def load_results(json_file):
    """Load results from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)

def create_baseline_table(simple_results, chunked_results, output_dir):
    """
    Part 1: Create baseline comparison table for default configuration.
    Default: L1I=32KiB, L1D=64KiB, L2=512KiB, L1_assoc=8, L2_assoc=16
    """
    # Find baseline configuration in results
    baseline_config = {
        'l1i_size': '32KiB',
        'l1d_size': '64KiB',
        'l2_size': '512KiB',
        'l1_assoc': 8,
        'l2_assoc': 16
    }
    
    def find_baseline(results):
        for result in results:
            config = result['config']
            if (config['l1i_size'] == baseline_config['l1i_size'] and
                config['l1d_size'] == baseline_config['l1d_size'] and
                config['l2_size'] == baseline_config['l2_size'] and
                config['l1_assoc'] == baseline_config['l1_assoc'] and
                config['l2_assoc'] == baseline_config['l2_assoc']):
                return result['stats']
        return None
    
    simple_baseline = find_baseline(simple_results)
    chunked_baseline = find_baseline(chunked_results)
    
    if not simple_baseline or not chunked_baseline:
        print("Warning: Baseline configuration not found in results!")
        return None
    
    # Create comparison table
    metrics = [
        'sim_ticks',
        'sim_seconds',
        'sim_insts',
        'ipc',
        'cpi',
        'l1d_accesses',
        'l1d_misses',
        'l1d_miss_rate',
        'l1d_hit_rate',
        'l1i_accesses',
        'l1i_misses',
        'l1i_miss_rate',
        'l1i_hit_rate',
        'l2_accesses',
        'l2_misses',
        'l2_miss_rate',
        'l2_hit_rate'
    ]
    
    data = {
        'Metric': metrics,
        'Simple MergeSort': [simple_baseline.get(m, 'N/A') for m in metrics],
        'Chunked MergeSort': [chunked_baseline.get(m, 'N/A') for m in metrics],
    }
    
    df = pd.DataFrame(data)
    
    # Add difference/ratio column
    def calc_diff(row):
        try:
            simple_val = float(row['Simple MergeSort'])
            chunked_val = float(row['Chunked MergeSort'])
            if simple_val != 0:
                ratio = chunked_val / simple_val
                return f"{ratio:.3f}x"
            return "N/A"
        except:
            return "N/A"
    
    df['Chunked/Simple Ratio'] = df.apply(calc_diff, axis=1)
    
    # Save to CSV
    csv_path = output_dir / 'part1_baseline_comparison.csv'
    df.to_csv(csv_path, index=False)
    print(f"Baseline comparison table saved: {csv_path}")
    
    # Also save a formatted text version
    txt_path = output_dir / 'part1_baseline_comparison.txt'
    with open(txt_path, 'w') as f:
        f.write("PART 1: BASELINE COMPARISON\n")
        f.write("Default Configuration: L1I=32KiB/8-way, L1D=64KiB/8-way, L2=512KiB/16-way\n")
        f.write(df.to_string(index=False))
        f.write("\n\n")
    print(f"Baseline comparison text saved: {txt_path}")
    
    return df

def create_full_results_table(simple_results, chunked_results, output_dir):
    """
    Part 2: Create comprehensive results table for all configurations.
    """
    # Combine both results
    all_results = []
    
    for result in simple_results:
        row = {
            'variant': 'simple',
            **result['config'],
            **result['stats']
        }
        all_results.append(row)
    
    for result in chunked_results:
        row = {
            'variant': 'chunked',
            **result['config'],
            **result['stats']
        }
        all_results.append(row)
    
    df = pd.DataFrame(all_results)
    
    # Select key columns for the summary table
    key_columns = [
        'variant', 'l1i_size', 'l1d_size', 'l2_size', 'l1_assoc', 'l2_assoc',
        'sim_ticks', 'ipc', 'cpi', 
        'l1d_miss_rate', 'l1i_miss_rate', 'l2_miss_rate',
        'l1d_hit_rate', 'l1i_hit_rate', 'l2_hit_rate',
        'l1d_misses', 'l2_misses'
    ]
    
    df_summary = df[key_columns].copy()
    
    # Save full table
    csv_path = output_dir / 'part2_full_results.csv'
    df_summary.to_csv(csv_path, index=False)
    print(f"Full results table saved: {csv_path}")
    
    return df

def find_top_configs(df, output_dir, n=3):
    """
    Part 2: Find top N configurations ranked by IPC for each variant.
    """
    results = {}
    
    for variant in ['simple', 'chunked']:
        variant_df = df[df['variant'] == variant].copy()
        top_n = variant_df.nlargest(n, 'ipc')
        
        results[variant] = top_n[[
            'l1i_size', 'l1d_size', 'l2_size', 'l1_assoc', 'l2_assoc',
            'ipc', 'cpi', 'sim_ticks', 'l1d_miss_rate', 'l2_miss_rate'
        ]]
    
    # Save to file
    txt_path = output_dir / 'part2_top_configs.txt'
    with open(txt_path, 'w') as f:
        f.write("PART 2: TOP 3 CONFIGURATIONS RANKED BY IPC\n")        
        for variant in ['simple', 'chunked']:
            f.write(f"\n{variant.upper()} MERGESORT - TOP 3 CONFIGURATIONS:\n")
            f.write("-"*80 + "\n")
            f.write(results[variant].to_string(index=False))
            f.write("\n\n")
    
    print(f"✓ Top configurations saved: {txt_path}")
    
    # Also save as CSV
    for variant in ['simple', 'chunked']:
        csv_path = output_dir / f'part2_top3_{variant}.csv'
        results[variant].to_csv(csv_path, index=False)
    
    return results

def create_plots(df, output_dir):
    """
    Part 2: Create required plots for analysis.
    """
    plots_dir = output_dir / 'plots'
    plots_dir.mkdir(exist_ok=True)
    
    # Plot 1: L2 miss rate vs L2 size (for both variants)
    plt.figure(figsize=(12, 6))
    for variant in ['simple', 'chunked']:
        variant_df = df[df['variant'] == variant]
        # Group by L2 size and calculate mean miss rate
        grouped = variant_df.groupby('l2_size')['l2_miss_rate'].mean()
        sizes_order = ['256KiB', '512KiB', '1024KiB', '1MB']
        grouped = grouped.reindex([s for s in sizes_order if s in grouped.index])
        plt.plot(grouped.index, grouped.values, marker='o', label=variant.capitalize(), linewidth=2, markersize=8)
    
    plt.xlabel('L2 Cache Size', fontsize=12)
    plt.ylabel('L2 Miss Rate', fontsize=12)
    plt.title('L2 Miss Rate vs L2 Cache Size', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'plot1_l2_miss_rate_vs_l2_size.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot 1 saved: L2 miss rate vs L2 size")
    
    # Plot 2: IPC vs L1D size (for both variants)
    plt.figure(figsize=(12, 6))
    for variant in ['simple', 'chunked']:
        variant_df = df[df['variant'] == variant]
        grouped = variant_df.groupby('l1d_size')['ipc'].mean()
        sizes_order = ['32KiB', '64KiB', '128KiB']
        grouped = grouped.reindex([s for s in sizes_order if s in grouped.index])
        plt.plot(grouped.index, grouped.values, marker='s', label=variant.capitalize(), linewidth=2, markersize=8)
    
    plt.xlabel('L1 Data Cache Size', fontsize=12)
    plt.ylabel('Instructions Per Cycle (IPC)', fontsize=12)
    plt.title('IPC vs L1 Data Cache Size', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'plot2_ipc_vs_l1d_size.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot 2 saved: IPC vs L1D size")
    
    # Plot 3: L1D hit rate vs associativity (for both variants)
    plt.figure(figsize=(12, 6))
    for variant in ['simple', 'chunked']:
        variant_df = df[df['variant'] == variant]
        grouped = variant_df.groupby('l1_assoc')['l1d_hit_rate'].mean()
        plt.plot(grouped.index, grouped.values, marker='^', label=variant.capitalize(), linewidth=2, markersize=8)
    
    plt.xlabel('L1 Cache Associativity (ways)', fontsize=12)
    plt.ylabel('L1 Data Cache Hit Rate', fontsize=12)
    plt.title('L1D Hit Rate vs Cache Associativity', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'plot3_l1d_hit_rate_vs_associativity.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot 3 saved: L1D hit rate vs associativity")
    
    # Plot 4: Simple vs Chunked comparison - multiple metrics
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Subplot 1: IPC comparison
    simple_df = df[df['variant'] == 'simple']
    chunked_df = df[df['variant'] == 'chunked']
    
    ax = axes[0, 0]
    configs = range(len(simple_df))
    ax.scatter(configs, simple_df['ipc'].values, alpha=0.6, label='Simple', s=50)
    ax.scatter(configs, chunked_df['ipc'].values, alpha=0.6, label='Chunked', s=50)
    ax.set_xlabel('Configuration Index', fontsize=10)
    ax.set_ylabel('IPC', fontsize=10)
    ax.set_title('IPC Comparison', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Subplot 2: L1D miss rate comparison
    ax = axes[0, 1]
    ax.scatter(configs, simple_df['l1d_miss_rate'].values, alpha=0.6, label='Simple', s=50)
    ax.scatter(configs, chunked_df['l1d_miss_rate'].values, alpha=0.6, label='Chunked', s=50)
    ax.set_xlabel('Configuration Index', fontsize=10)
    ax.set_ylabel('L1D Miss Rate', fontsize=10)
    ax.set_title('L1D Miss Rate Comparison', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Subplot 3: L2 miss rate comparison
    ax = axes[1, 0]
    ax.scatter(configs, simple_df['l2_miss_rate'].values, alpha=0.6, label='Simple', s=50)
    ax.scatter(configs, chunked_df['l2_miss_rate'].values, alpha=0.6, label='Chunked', s=50)
    ax.set_xlabel('Configuration Index', fontsize=10)
    ax.set_ylabel('L2 Miss Rate', fontsize=10)
    ax.set_title('L2 Miss Rate Comparison', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Subplot 4: Simulation ticks comparison
    ax = axes[1, 1]
    ax.scatter(configs, simple_df['sim_ticks'].values, alpha=0.6, label='Simple', s=50)
    ax.scatter(configs, chunked_df['sim_ticks'].values, alpha=0.6, label='Chunked', s=50)
    ax.set_xlabel('Configuration Index', fontsize=10)
    ax.set_ylabel('Simulation Ticks', fontsize=10)
    ax.set_title('Execution Time Comparison', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(plots_dir / 'plot4_simple_vs_chunked_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot 4 saved: Simple vs Chunked comparison")
    
    # Additional Plot 5: Heatmap of IPC for different L1D and L2 sizes (Simple)
    plt.figure(figsize=(10, 8))
    simple_pivot = simple_df.pivot_table(values='ipc', index='l2_size', columns='l1d_size', aggfunc='mean')
    sizes_order_l1d = ['32KiB', '64KiB', '128KiB']
    sizes_order_l2 = ['256KiB', '512KiB', '1024KiB', '1MB']
    simple_pivot = simple_pivot.reindex(index=[s for s in sizes_order_l2 if s in simple_pivot.index],
                                        columns=[s for s in sizes_order_l1d if s in simple_pivot.columns])
    sns.heatmap(simple_pivot, annot=True, fmt='.3f', cmap='YlOrRd', cbar_kws={'label': 'IPC'})
    plt.title('Simple MergeSort: IPC Heatmap (L1D vs L2 Size)', fontsize=14, fontweight='bold')
    plt.xlabel('L1D Cache Size', fontsize=12)
    plt.ylabel('L2 Cache Size', fontsize=12)
    plt.tight_layout()
    plt.savefig(plots_dir / 'plot5_simple_ipc_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot 5 saved: Simple IPC heatmap")
    
    # Additional Plot 6: Heatmap of IPC for different L1D and L2 sizes (Chunked)
    plt.figure(figsize=(10, 8))
    chunked_pivot = chunked_df.pivot_table(values='ipc', index='l2_size', columns='l1d_size', aggfunc='mean')
    chunked_pivot = chunked_pivot.reindex(index=[s for s in sizes_order_l2 if s in chunked_pivot.index],
                                          columns=[s for s in sizes_order_l1d if s in chunked_pivot.columns])
    sns.heatmap(chunked_pivot, annot=True, fmt='.3f', cmap='YlGnBu', cbar_kws={'label': 'IPC'})
    plt.title('Chunked MergeSort: IPC Heatmap (L1D vs L2 Size)', fontsize=14, fontweight='bold')
    plt.xlabel('L1D Cache Size', fontsize=12)
    plt.ylabel('L2 Cache Size', fontsize=12)
    plt.tight_layout()
    plt.savefig(plots_dir / 'plot6_chunked_ipc_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot 6 saved: Chunked IPC heatmap")
    
    print(f"\nAll plots saved in: {plots_dir}/")

def generate_summary_report(baseline_df, top_configs, output_dir):
    """
    Generate a comprehensive summary report.
    """
    report_path = output_dir / 'ANALYSIS_SUMMARY.txt'
    
    with open(report_path, 'w') as f:
        f.write("PROBLEM 2: MERGESORT CACHE ANALYSIS - SUMMARY REPORT\n")
        
        f.write("PART 1: BASELINE COMPARISON\n")
        f.write("-"*80 + "\n")
        f.write("Default Configuration: L1I=32KiB/8-way, L1D=64KiB/8-way, L2=512KiB/16-way\n\n")
        if baseline_df is not None:
            f.write(baseline_df.to_string(index=False))
        f.write("\n\n")
        
        f.write("PART 2: TOP CONFIGURATIONS BY IPC\n")
        f.write("-"*80 + "\n\n")
        for variant in ['simple', 'chunked']:
            f.write(f"{variant.upper()} MERGESORT - TOP 3:\n")
            f.write(top_configs[variant].to_string(index=False))
            f.write("\n\n")
        
        f.write("DELIVERABLES GENERATED:\n")
        f.write("1. part1_baseline_comparison.csv - Baseline stats table\n")
        f.write("2. part2_full_results.csv - Complete sweep results\n")
        f.write("3. part2_top3_simple.csv - Top 3 configs for simple mergesort\n")
        f.write("4. part2_top3_chunked.csv - Top 3 configs for chunked mergesort\n")
        f.write("5. plots/ directory - All required plots\n")
        f.write("   - plot1_l2_miss_rate_vs_l2_size.png\n")
        f.write("   - plot2_ipc_vs_l1d_size.png\n")
        f.write("   - plot3_l1d_hit_rate_vs_associativity.png\n")
        f.write("   - plot4_simple_vs_chunked_comparison.png\n")
        f.write("   - plot5_simple_ipc_heatmap.png\n")
        f.write("   - plot6_chunked_ipc_heatmap.png\n")
        f.write("\n")
    
    print(f"\nSummary report saved: {report_path}")

def main():
    parser = argparse.ArgumentParser(description='Analyze merge sort simulation results')
    parser.add_argument('--simple', type=str, default='sweep_result/results_simple.json',
                        help='Path to simple results JSON file')
    parser.add_argument('--chunked', type=str, default='sweep_result/results_chunked.json',
                        help='Path to chunked results JSON file')
    parser.add_argument('--output', type=str, default='analysis',
                        help='Output directory for analysis results')
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    print("="*80)
    print("PROBLEM 2: MERGESORT CACHE ANALYSIS")
    print("="*80)
    
    # Load results
    print("\nLoading results...")
    simple_results = load_results(args.simple)
    chunked_results = load_results(args.chunked)
    print(f"Loaded {len(simple_results)} simple configurations")
    print(f"Loaded {len(chunked_results)} chunked configurations")
    
    # Part 1: Baseline comparison
    print("\n" + "="*80)
    print("PART 1: BASELINE COMPARISON")
    print("="*80)
    baseline_df = create_baseline_table(simple_results, chunked_results, output_dir)
    
    # Part 2: Full sweep analysis
    print("\n" + "="*80)
    print("PART 2: CACHE OPTIMIZATION SWEEP")
    print("="*80)
    df = create_full_results_table(simple_results, chunked_results, output_dir)
    
    # Find top configurations
    print("\nFinding top configurations...")
    top_configs = find_top_configs(df, output_dir)
    
    # Create plots
    print("\nGenerating plots...")
    create_plots(df, output_dir)
    
    # Generate summary report
    print("\nGenerating summary report...")
    generate_summary_report(baseline_df, top_configs, output_dir)
    
    print("ANALYSIS COMPLETE!")
    print(f"\nAll results saved in: {output_dir}/")
    print("\nNext steps:")
    print("1. Review the baseline comparison table (part1_baseline_comparison.csv)")
    print("2. Examine the plots in the plots/ directory")
    print("3. Check top configurations (part2_top3_*.csv)")
    print("4. Write your analysis based on the data (200-300 words for Part 1)")
    print("\n")

if __name__ == '__main__':
    main()
