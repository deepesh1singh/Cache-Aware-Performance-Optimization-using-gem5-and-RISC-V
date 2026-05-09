#!/usr/bin/env python3
"""
Analysis script for gem5 cache parameter sweep results.
Generates tables and plots required by the problem statement.
"""

import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path


def load_results(json_file):
    """Load results from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)


def create_results_table(results, output_dir):
    """Create a comprehensive results table."""
    df = pd.DataFrame(results)
    
    # Flatten config dict into separate columns
    config_df = pd.json_normalize(df['config'])
    df = pd.concat([df.drop('config', axis=1), config_df], axis=1)
    
    # Select key columns
    columns = [
        'l1i_size', 'l1d_size', 'l2_size',
        'l1i_assoc', 'l1d_assoc', 'l2_assoc',
        'sim_ticks', 'sim_seconds', 'cpi', 'ipc',
        'l1d_hit_rate', 'l1i_hit_rate', 'l2_hit_rate',
        'l1d_misses', 'l2_misses'
    ]
    
    df_summary = df[columns].copy()
    
    # Save to CSV
    csv_path = output_dir / 'full_results_table.csv'
    df_summary.to_csv(csv_path, index=False)
    print(f"Saved full results table: {csv_path}")
    
    return df


def generate_summary_statistics(df, output_dir):
    """Generate summary statistics for key metrics."""
    metrics = ['sim_ticks', 'cpi', 'ipc', 'l1d_hit_rate', 'l1i_hit_rate', 'l2_hit_rate']
    
    summary_stats = df[metrics].describe().T
    summary_stats = summary_stats[['mean', 'min', 'max', 'std']]
    
    # Save to CSV
    stats_path = output_dir / 'summary_statistics.csv'
    summary_stats.to_csv(stats_path)
    print(f"Saved summary statistics: {stats_path}")
    
    # Print to console
    print("SUMMARY STATISTICS")
    print(summary_stats.to_string())
    
    return summary_stats


def find_top_configurations(df, output_dir):
    """Find top 3 configurations for different metrics."""
    
    # Top 3 by lowest execution time
    top_exec_time = df.nsmallest(3, 'sim_ticks')[
        ['l1i_size', 'l1d_size', 'l2_size', 'l1i_assoc', 'l1d_assoc', 'l2_assoc', 
         'sim_ticks', 'sim_seconds']
    ]
    
    # Top 3 by highest L1D hit rate
    top_l1d_hit = df.nlargest(3, 'l1d_hit_rate')[
        ['l1i_size', 'l1d_size', 'l2_size', 'l1i_assoc', 'l1d_assoc', 'l2_assoc',
         'l1d_hit_rate', 'sim_ticks']
    ]
    
    # Top 3 by highest L2 hit rate
    top_l2_hit = df.nlargest(3, 'l2_hit_rate')[
        ['l1i_size', 'l1d_size', 'l2_size', 'l1i_assoc', 'l1d_assoc', 'l2_assoc',
         'l2_hit_rate', 'sim_ticks']
    ]
    
    # Save to files
    top_exec_time.to_csv(output_dir / 'top3_execution_time.csv', index=False)
    top_l1d_hit.to_csv(output_dir / 'top3_l1d_hit_rate.csv', index=False)
    top_l2_hit.to_csv(output_dir / 'top3_l2_hit_rate.csv', index=False)
    
    print("TOP 3 CONFIGURATIONS BY LOWEST EXECUTION TIME")
    print(top_exec_time.to_string(index=False))
    
    print("TOP 3 CONFIGURATIONS BY HIGHEST L1D HIT RATE")
    print(top_l1d_hit.to_string(index=False))
    
    print("TOP 3 CONFIGURATIONS BY HIGHEST L2 HIT RATE")
    print(top_l2_hit.to_string(index=False))


def plot_l1d_size_impact(df, output_dir):
    """Plot impact of L1D cache size."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Group by L1D size
    grouped = df.groupby('l1d_size').agg({
        'sim_ticks': ['mean', 'std'],
        'l1d_hit_rate': ['mean', 'std']
    })
    
    l1d_sizes = ['16kB', '32kB', '64kB']
    
    # Plot execution time
    means = [grouped.loc[size, ('sim_ticks', 'mean')] for size in l1d_sizes]
    stds = [grouped.loc[size, ('sim_ticks', 'std')] for size in l1d_sizes]
    
    bars0 = axes[0].bar(l1d_sizes, means, yerr=stds, capsize=5, alpha=0.7, color='steelblue')
    axes[0].set_xlabel('L1D Cache Size', fontsize=12)
    axes[0].set_ylabel('Execution Time (ticks)', fontsize=12)
    axes[0].set_title('L1D Size vs Execution Time', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, mean in zip(bars0, means):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{mean:.2e}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot hit rate
    means = [grouped.loc[size, ('l1d_hit_rate', 'mean')] for size in l1d_sizes]
    stds = [grouped.loc[size, ('l1d_hit_rate', 'std')] for size in l1d_sizes]
    
    bars1 = axes[1].bar(l1d_sizes, means, yerr=stds, capsize=5, alpha=0.7, color='coral')
    axes[1].set_xlabel('L1D Cache Size', fontsize=12)
    axes[1].set_ylabel('L1D Hit Rate', fontsize=12)
    axes[1].set_title('L1D Size vs Hit Rate', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_ylim([0, 1])
    
    # Add value labels on bars
    for bar, mean in zip(bars1, means):
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2., height,
                    f'{mean:.4f}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plot_path = output_dir / 'l1d_size_impact.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {plot_path}")
    plt.close()


def plot_l2_size_impact(df, output_dir):
    """Plot impact of L2 cache size."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Group by L2 size
    grouped = df.groupby('l2_size').agg({
        'sim_ticks': ['mean', 'std'],
        'l2_hit_rate': ['mean', 'std']
    })
    
    # Get all L2 sizes that exist in data
    l2_sizes = [s for s in ['128kB', '256kB', '512kB', '1MB'] if s in grouped.index]
    
    # Plot execution time
    means = [grouped.loc[size, ('sim_ticks', 'mean')] for size in l2_sizes]
    stds = [grouped.loc[size, ('sim_ticks', 'std')] for size in l2_sizes]
    
    bars0 = axes[0].bar(l2_sizes, means, yerr=stds, capsize=5, alpha=0.7, color='mediumseagreen')
    axes[0].set_xlabel('L2 Cache Size', fontsize=12)
    axes[0].set_ylabel('Execution Time (ticks)', fontsize=12)
    axes[0].set_title('L2 Size vs Execution Time', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, mean in zip(bars0, means):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{mean:.2e}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot hit rate
    means = [grouped.loc[size, ('l2_hit_rate', 'mean')] for size in l2_sizes]
    stds = [grouped.loc[size, ('l2_hit_rate', 'std')] for size in l2_sizes]
    
    bars1 = axes[1].bar(l2_sizes, means, yerr=stds, capsize=5, alpha=0.7, color='mediumpurple')
    axes[1].set_xlabel('L2 Cache Size', fontsize=12)
    axes[1].set_ylabel('L2 Hit Rate', fontsize=12)
    axes[1].set_title('L2 Size vs Hit Rate', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_ylim([0, 1])
    
    # Add value labels on bars
    for bar, mean in zip(bars1, means):
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2., height,
                    f'{mean:.4f}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plot_path = output_dir / 'l2_size_impact.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {plot_path}")
    plt.close()


def plot_associativity_impact(df, output_dir):
    """Plot impact of cache associativity."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # L1D Associativity impact
    grouped_l1d = df.groupby('l1d_assoc').agg({
        'sim_ticks': ['mean', 'std'],
        'l1d_hit_rate': ['mean', 'std']
    })
    
    assocs_l1d = sorted(df['l1d_assoc'].unique())
    
    # L1D Assoc vs Execution Time
    means = [grouped_l1d.loc[a, ('sim_ticks', 'mean')] for a in assocs_l1d]
    stds = [grouped_l1d.loc[a, ('sim_ticks', 'std')] for a in assocs_l1d]
    bars = axes[0, 0].bar([str(a) for a in assocs_l1d], means, yerr=stds, capsize=5, 
                   alpha=0.7, color='steelblue')
    axes[0, 0].set_xlabel('L1D Associativity', fontsize=12)
    axes[0, 0].set_ylabel('Execution Time (ticks)', fontsize=12)
    axes[0, 0].set_title('L1D Associativity vs Execution Time', fontsize=12, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    for bar, mean in zip(bars, means):
        height = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width()/2., height,
                       f'{mean:.2e}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # L1D Assoc vs Hit Rate
    means = [grouped_l1d.loc[a, ('l1d_hit_rate', 'mean')] for a in assocs_l1d]
    stds = [grouped_l1d.loc[a, ('l1d_hit_rate', 'std')] for a in assocs_l1d]
    bars = axes[0, 1].bar([str(a) for a in assocs_l1d], means, yerr=stds, capsize=5,
                   alpha=0.7, color='coral')
    axes[0, 1].set_xlabel('L1D Associativity', fontsize=12)
    axes[0, 1].set_ylabel('L1D Hit Rate', fontsize=12)
    axes[0, 1].set_title('L1D Associativity vs Hit Rate', fontsize=12, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_ylim([0, 1])
    for bar, mean in zip(bars, means):
        height = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width()/2., height,
                       f'{mean:.4f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # L2 Associativity impact
    grouped_l2 = df.groupby('l2_assoc').agg({
        'sim_ticks': ['mean', 'std'],
        'l2_hit_rate': ['mean', 'std']
    })
    
    assocs_l2 = sorted(df['l2_assoc'].unique())
    
    # L2 Assoc vs Execution Time
    means = [grouped_l2.loc[a, ('sim_ticks', 'mean')] for a in assocs_l2]
    stds = [grouped_l2.loc[a, ('sim_ticks', 'std')] for a in assocs_l2]
    bars = axes[1, 0].bar([str(a) for a in assocs_l2], means, yerr=stds, capsize=5,
                   alpha=0.7, color='mediumseagreen')
    axes[1, 0].set_xlabel('L2 Associativity', fontsize=12)
    axes[1, 0].set_ylabel('Execution Time (ticks)', fontsize=12)
    axes[1, 0].set_title('L2 Associativity vs Execution Time', fontsize=12, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    for bar, mean in zip(bars, means):
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                       f'{mean:.2e}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # L2 Assoc vs Hit Rate
    means = [grouped_l2.loc[a, ('l2_hit_rate', 'mean')] for a in assocs_l2]
    stds = [grouped_l2.loc[a, ('l2_hit_rate', 'std')] for a in assocs_l2]
    bars = axes[1, 1].bar([str(a) for a in assocs_l2], means, yerr=stds, capsize=5,
                   alpha=0.7, color='mediumpurple')
    axes[1, 1].set_xlabel('L2 Associativity', fontsize=12)
    axes[1, 1].set_ylabel('L2 Hit Rate', fontsize=12)
    axes[1, 1].set_title('L2 Associativity vs Hit Rate', fontsize=12, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_ylim([0, 1])
    for bar, mean in zip(bars, means):
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                       f'{mean:.4f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    plt.tight_layout()
    plot_path = output_dir / 'associativity_impact.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {plot_path}")
    plt.close()


def plot_performance_heatmap(df, output_dir):
    """Create heatmap showing performance across L1D and L2 sizes."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Create pivot table for execution time
    pivot_time = df.pivot_table(
        values='sim_ticks',
        index='l1d_size',
        columns='l2_size',
        aggfunc='mean'
    )
    
    # Reorder to ensure proper order
    pivot_time = pivot_time.reindex(['16kB', '32kB', '64kB'])
    # Include all L2 sizes that exist in data
    l2_cols = [col for col in ['128kB', '256kB', '512kB', '1MB'] if col in pivot_time.columns]
    pivot_time = pivot_time[l2_cols]
    
    # Create pivot table for L1D hit rate
    pivot_hit = df.pivot_table(
        values='l1d_hit_rate',
        index='l1d_size',
        columns='l2_size',
        aggfunc='mean'
    )
    
    pivot_hit = pivot_hit.reindex(['16kB', '32kB', '64kB'])
    pivot_hit = pivot_hit[l2_cols]
    
    # Plot execution time heatmap
    im1 = axes[0].imshow(pivot_time.values, cmap='YlOrRd', aspect='auto')
    axes[0].set_xticks(range(len(pivot_time.columns)))
    axes[0].set_yticks(range(len(pivot_time.index)))
    axes[0].set_xticklabels(pivot_time.columns)
    axes[0].set_yticklabels(pivot_time.index)
    axes[0].set_xlabel('L2 Cache Size', fontsize=12)
    axes[0].set_ylabel('L1D Cache Size', fontsize=12)
    axes[0].set_title('Execution Time Heatmap\n(Lower is Better)', fontsize=14, fontweight='bold')
    
    # Add text annotations
    for i in range(len(pivot_time.index)):
        for j in range(len(pivot_time.columns)):
            text = axes[0].text(j, i, f'{pivot_time.values[i, j]:.2e}',
                              ha="center", va="center", color="black", fontsize=9)
    
    plt.colorbar(im1, ax=axes[0], label='Execution Time (ticks)')
    
    # Plot hit rate heatmap
    im2 = axes[1].imshow(pivot_hit.values, cmap='YlGn', aspect='auto', vmin=0, vmax=1)
    axes[1].set_xticks(range(len(pivot_hit.columns)))
    axes[1].set_yticks(range(len(pivot_hit.index)))
    axes[1].set_xticklabels(pivot_hit.columns)
    axes[1].set_yticklabels(pivot_hit.index)
    axes[1].set_xlabel('L2 Cache Size', fontsize=12)
    axes[1].set_ylabel('L1D Cache Size', fontsize=12)
    axes[1].set_title('L1D Hit Rate Heatmap\n(Higher is Better)', fontsize=14, fontweight='bold')
    
    # Add text annotations
    for i in range(len(pivot_hit.index)):
        for j in range(len(pivot_hit.columns)):
            text = axes[1].text(j, i, f'{pivot_hit.values[i, j]:.3f}',
                              ha="center", va="center", color="black", fontsize=9)
    
    plt.colorbar(im2, ax=axes[1], label='L1D Hit Rate')
    
    plt.tight_layout()
    plot_path = output_dir / 'performance_heatmap.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {plot_path}")
    plt.close()


def plot_pareto_frontier(df, output_dir):
    """Plot Pareto frontier for execution time vs hit rate trade-off.
    
    Pareto-optimal configurations are those where you cannot improve one metric
    (execution time or hit rate) without making the other metric worse.
    These represent the best design trade-offs.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Scatter plot of all configurations
    scatter = ax.scatter(df['l1d_hit_rate'], df['sim_ticks'], 
                        c=df['l2_hit_rate'], cmap='viridis', 
                        s=100, alpha=0.6, edgecolors='black', linewidth=0.5,
                        label='All Configurations')
    
    # Find Pareto frontier (minimize time, maximize hit rate)
    # A point is Pareto-optimal if no other point dominates it
    # Point A dominates Point B if: A.hit_rate >= B.hit_rate AND A.time <= B.time (with at least one strict inequality)
    pareto_points = []
    
    for idx, row in df.iterrows():
        is_dominated = False
        for _, other_row in df.iterrows():
            # Check if other_row dominates row
            if (other_row['l1d_hit_rate'] >= row['l1d_hit_rate'] and 
                other_row['sim_ticks'] <= row['sim_ticks'] and
                (other_row['l1d_hit_rate'] > row['l1d_hit_rate'] or 
                 other_row['sim_ticks'] < row['sim_ticks'])):
                is_dominated = True
                break
        
        if not is_dominated:
            pareto_points.append(row)
    
    if pareto_points:
        pareto_df = pd.DataFrame(pareto_points)
        pareto_df = pareto_df.sort_values('l1d_hit_rate')
        
        # Save Pareto-optimal configurations
        pareto_configs = pareto_df[['l1i_size', 'l1d_size', 'l2_size', 
                                     'l1i_assoc', 'l1d_assoc', 'l2_assoc',
                                     'sim_ticks', 'l1d_hit_rate', 'l2_hit_rate']].copy()
        pareto_path = output_dir / 'pareto_optimal_configs.csv'
        pareto_configs.to_csv(pareto_path, index=False)
        # Avoid Unicode symbols in console output for better Windows compatibility
        print(f"Saved Pareto-optimal configurations: {pareto_path}")
        print(f"Found {len(pareto_df)} Pareto-optimal configurations")
        
        # Plot the Pareto frontier line
        ax.plot(pareto_df['l1d_hit_rate'], pareto_df['sim_ticks'], 
               'r-', linewidth=2.5, label='Pareto Frontier', zorder=10, alpha=0.7)
        ax.scatter(pareto_df['l1d_hit_rate'], pareto_df['sim_ticks'],
                  c='red', s=250, marker='*', edgecolors='black', 
                  linewidth=1.5, label=f'Pareto Optimal ({len(pareto_df)} configs)', zorder=11)
        
        # Annotate key Pareto points (show up to 8 to avoid clutter)
        num_to_annotate = min(8, len(pareto_df))
        step = max(1, len(pareto_df) // num_to_annotate)
        for i, (idx, row) in enumerate(pareto_df.iterrows()):
            if i % step == 0 or i == len(pareto_df) - 1:
                config_label = f"{row['l1d_size']}/{row['l2_size']}"
                ax.annotate(config_label, 
                           (row['l1d_hit_rate'], row['sim_ticks']),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.8,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
    
    ax.set_xlabel('L1D Hit Rate', fontsize=12)
    ax.set_ylabel('Execution Time (ticks)', fontsize=12)
    ax.set_title('Pareto Frontier: Optimal Performance-Hit Rate Trade-offs\n' +
                'Points on frontier cannot be improved without sacrificing another metric',
                fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='upper right')
    
    # Add text box explaining Pareto optimality
    textstr = 'Pareto-Optimal Configs:\nBest trade-offs where improving\none metric worsens another'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.colorbar(scatter, ax=ax, label='L2 Hit Rate')
    
    plt.tight_layout()
    plot_path = output_dir / 'pareto_frontier.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    # Avoid Unicode symbols in console output for better Windows compatibility
    print(f"Saved plot: {plot_path}")
    plt.close()
    
    return pareto_df


def extract_single_parameter_analysis(df, output_dir, param='l2_size', base_config=None):
    """Extract single parameter sweep from full sweep data."""
    if base_config is None:
        base_config = {
            'l1i_size': '16kB',
            'l1d_size': '16kB',
            'l2_size': '256kB',
            'l1i_assoc': 4,
            'l1d_assoc': 4,
            'l2_assoc': 8
        }
    
    # Filter for base configuration except the varying parameter
    filtered_df = df.copy()
    for key, value in base_config.items():
        if key != param:
            filtered_df = filtered_df[filtered_df[key] == value]
    
    # Create plots for the single parameter
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    if param in ['l1d_size', 'l2_size']:
        param_values = sorted(filtered_df[param].unique(), key=lambda x: int(x[:-2]))
        hit_rate_col = 'l1d_hit_rate' if param == 'l1d_size' else 'l2_hit_rate'
    else:
        param_values = sorted(filtered_df[param].unique())
        param_values = [str(v) for v in param_values]
        hit_rate_col = 'l1d_hit_rate' if 'l1' in param else 'l2_hit_rate'
    
    # Execution time plot
    exec_times = [filtered_df[filtered_df[param] == (int(v) if isinstance(v, str) and v.isdigit() else v)]['sim_ticks'].values[0] 
                  if not isinstance(v, str) else filtered_df[filtered_df[param] == v]['sim_ticks'].values[0] 
                  for v in (param_values if param in ['l1d_size', 'l2_size'] else [int(v) if v.isdigit() else v for v in param_values])]
    
    axes[0].plot(range(len(param_values)), exec_times, 'o-', linewidth=2, markersize=8, color='steelblue')
    axes[0].set_xticks(range(len(param_values)))
    axes[0].set_xticklabels(param_values)
    axes[0].set_xlabel(param.replace('_', ' ').title(), fontsize=12)
    axes[0].set_ylabel('Execution Time (ticks)', fontsize=12)
    axes[0].set_title(f'{param.replace("_", " ").title()} vs Execution Time', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # Hit rate plot
    hit_rates = [filtered_df[filtered_df[param] == (int(v) if isinstance(v, str) and v.isdigit() else v)][hit_rate_col].values[0] 
                 if not isinstance(v, str) else filtered_df[filtered_df[param] == v][hit_rate_col].values[0] 
                 for v in (param_values if param in ['l1d_size', 'l2_size'] else [int(v) if v.isdigit() else v for v in param_values])]
    
    axes[1].plot(range(len(param_values)), hit_rates, 'o-', linewidth=2, markersize=8, color='coral')
    axes[1].set_xticks(range(len(param_values)))
    axes[1].set_xticklabels(param_values)
    axes[1].set_xlabel(param.replace('_', ' ').title(), fontsize=12)
    axes[1].set_ylabel('Hit Rate', fontsize=12)
    axes[1].set_title(f'{param.replace("_", " ").title()} vs Hit Rate', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_ylim([0, 1])
    
    plt.tight_layout()
    plot_path = output_dir / f'single_param_{param}.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    # Avoid Unicode symbols in console output for better Windows compatibility
    print(f"Saved single parameter plot: {plot_path}")
    plt.close()
    
    # Save table
    table_path = output_dir / f'single_param_{param}_table.csv'
    filtered_df[['l1i_size', 'l1d_size', 'l2_size', 'l1i_assoc', 'l1d_assoc', 'l2_assoc',
                 'sim_ticks', hit_rate_col]].to_csv(table_path, index=False)
    print(f"Saved single parameter table: {table_path}")


def create_interaction_heatmaps(df, output_dir):
    """Create 2D heatmaps showing parameter interactions (Part 3)."""
    
    plots_dir = output_dir / 'interaction_plots'
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    # Define proper ordering for sizes
    l1d_size_order = ['16kB', '32kB', '64kB']
    l2_size_order = ['128kB', '256kB', '512kB', '1MB']
    
    # 1. L1D Size vs L2 Size (averaged over associativities)
    print("  Generating L1D Size vs L2 Size heatmap...")
    pivot = df.pivot_table(values='ipc', index='l2_size', columns='l1d_size', aggfunc='mean')
    # Reorder to ensure monotonic axes
    pivot = pivot.reindex(index=l2_size_order, columns=l1d_size_order)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.4f', cmap='YlOrRd', cbar_kws={'label': 'IPC'})
    plt.title('IPC: L1D Size vs L2 Size Interaction', fontsize=14, fontweight='bold')
    plt.xlabel('L1D Cache Size', fontsize=12)
    plt.ylabel('L2 Cache Size', fontsize=12)
    plt.tight_layout()
    plt.savefig(plots_dir / 'interaction_l1d_l2_size.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. L1D Assoc vs L2 Assoc (averaged over sizes)
    print("  Generating L1D Assoc vs L2 Assoc heatmap...")
    pivot = df.pivot_table(values='ipc', index='l2_assoc', columns='l1d_assoc', aggfunc='mean')
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.4f', cmap='YlGnBu', cbar_kws={'label': 'IPC'})
    plt.title('IPC: L1D Assoc vs L2 Assoc Interaction', fontsize=14, fontweight='bold')
    plt.xlabel('L1D Associativity', fontsize=12)
    plt.ylabel('L2 Associativity', fontsize=12)
    plt.tight_layout()
    plt.savefig(plots_dir / 'interaction_l1d_l2_assoc.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. L1D Size vs L1D Assoc
    print("  Generating L1D Size vs L1D Assoc heatmap...")
    pivot = df.pivot_table(values='l1d_hit_rate', index='l1d_assoc', columns='l1d_size', aggfunc='mean')
    # Reorder columns
    pivot = pivot.reindex(columns=l1d_size_order)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.4f', cmap='Greens', cbar_kws={'label': 'L1D Hit Rate'})
    plt.title('L1D Hit Rate: Size vs Associativity', fontsize=14, fontweight='bold')
    plt.xlabel('L1D Cache Size', fontsize=12)
    plt.ylabel('L1D Associativity', fontsize=12)
    plt.tight_layout()
    plt.savefig(plots_dir / 'interaction_l1d_size_assoc.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. L2 Size vs L2 Assoc
    print("  Generating L2 Size vs L2 Assoc heatmap...")
    pivot = df.pivot_table(values='l2_hit_rate', index='l2_assoc', columns='l2_size', aggfunc='mean')
    # Reorder columns
    pivot = pivot.reindex(columns=l2_size_order)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.4f', cmap='Blues', cbar_kws={'label': 'L2 Hit Rate'})
    plt.title('L2 Hit Rate: Size vs Associativity', fontsize=14, fontweight='bold')
    plt.xlabel('L2 Cache Size', fontsize=12)
    plt.ylabel('L2 Associativity', fontsize=12)
    plt.tight_layout()
    plt.savefig(plots_dir / 'interaction_l2_size_assoc.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. Execution Time: L1D vs L2 Size
    print("  Generating Execution Time heatmap...")
    pivot = df.pivot_table(values='sim_ticks', index='l2_size', columns='l1d_size', aggfunc='mean')
    # Reorder to ensure monotonic axes
    pivot = pivot.reindex(index=l2_size_order, columns=l1d_size_order)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.2e', cmap='RdYlGn_r', cbar_kws={'label': 'Simulation Ticks'})
    plt.title('Execution Time: L1D Size vs L2 Size', fontsize=14, fontweight='bold')
    plt.xlabel('L1D Cache Size', fontsize=12)
    plt.ylabel('L2 Cache Size', fontsize=12)
    plt.tight_layout()
    plt.savefig(plots_dir / 'interaction_execution_time.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"All interaction plots saved in: {plots_dir}/")


def generate_design_recommendations(df, output_dir):
    """Generate design recommendation table based on analysis."""
    
    # Make a copy to avoid modifying original
    df_work = df.copy()
    
    # Calculate total cache size in KB
    def calc_total_cache_kb(row):
        l1i_kb = int(row['l1i_size'][:-2])
        l1d_kb = int(row['l1d_size'][:-2])
        l2_size = row['l2_size']
        if l2_size[-2:] == 'kB':
            l2_kb = int(l2_size[:-2])
        else:  # MB
            l2_kb = int(l2_size[:-2]) * 1024
        return l1i_kb + l1d_kb + l2_kb
    
    df_work['total_cache_kb'] = df_work.apply(calc_total_cache_kb, axis=1)
    
    # Find best configurations for different scenarios
    best_performance = df_work.nsmallest(1, 'sim_ticks').iloc[0]
    
    # Power-constrained: smallest total cache size with reasonable performance
    perf_threshold = best_performance['sim_ticks'] * 1.2
    reasonable_configs = df_work[df_work['sim_ticks'] <= perf_threshold]
    power_constrained = reasonable_configs.nsmallest(1, 'total_cache_kb').iloc[0]
    
    # Balanced: best performance per cache KB
    df_work['perf_per_kb'] = 1 / (df_work['sim_ticks'] * df_work['total_cache_kb'])
    balanced = df_work.nlargest(1, 'perf_per_kb').iloc[0]
    
    recommendations = pd.DataFrame([
        {
            'Scenario': 'High-Performance',
            'L1I': best_performance['l1i_size'],
            'L1D': best_performance['l1d_size'],
            'L2': best_performance['l2_size'],
            'L1_Assoc': f"{best_performance['l1i_assoc']}/{best_performance['l1d_assoc']}",
            'L2_Assoc': best_performance['l2_assoc'],
            'Exec_Time_ticks': int(best_performance['sim_ticks']),
            'Total_Cache_KB': int(best_performance['total_cache_kb']),
            'Justification': 'Maximizes performance with largest caches and optimal associativity'
        },
        {
            'Scenario': 'Power-Constrained',
            'L1I': power_constrained['l1i_size'],
            'L1D': power_constrained['l1d_size'],
            'L2': power_constrained['l2_size'],
            'L1_Assoc': f"{power_constrained['l1i_assoc']}/{power_constrained['l1d_assoc']}",
            'L2_Assoc': power_constrained['l2_assoc'],
            'Exec_Time_ticks': int(power_constrained['sim_ticks']),
            'Total_Cache_KB': int(power_constrained['total_cache_kb']),
            'Justification': 'Minimizes cache size while maintaining acceptable performance'
        },
        {
            'Scenario': 'Balanced',
            'L1I': balanced['l1i_size'],
            'L1D': balanced['l1d_size'],
            'L2': balanced['l2_size'],
            'L1_Assoc': f"{balanced['l1i_assoc']}/{balanced['l1d_assoc']}",
            'L2_Assoc': balanced['l2_assoc'],
            'Exec_Time_ticks': int(balanced['sim_ticks']),
            'Total_Cache_KB': int(balanced['total_cache_kb']),
            'Justification': 'Optimal performance-to-cost ratio'
        }
    ])
    
    rec_path = output_dir / 'design_recommendations.csv'
    recommendations.to_csv(rec_path, index=False)
    print(f"Saved design recommendations: {rec_path}")
    
    print("\n" + "="*70)
    print("DESIGN RECOMMENDATIONS")
    print("="*70)
    print(recommendations.to_string(index=False))
    print("="*70 + "\n")
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(
        description='Analyze gem5 cache parameter sweep results'
    )
    parser.add_argument(
        'results_json',
        help='Path to results.json file from cache sweep'
    )
    parser.add_argument(
        '--output',
        default='analysis_output',
        help='Output directory for plots and tables (default: analysis_output)'
    )
    parser.add_argument(
        '--single-param',
        choices=['l1d_size', 'l2_size', 'l1_assoc', 'l2_assoc'],
        help='Extract single parameter analysis (optional)'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("GEM5 CACHE PARAMETER SWEEP ANALYSIS")
    print("="*70)
    print(f"Input file: {args.results_json}")
    print(f"Output directory: {output_dir}")
    print("="*70 + "\n")
    
    # Load results
    print("Loading results...")
    results = load_results(args.results_json)
    print(f"Loaded {len(results)} configurations\n")
    
    # Create results table
    print("Generating results table...")
    df = create_results_table(results, output_dir)
    
    # Generate summary statistics
    print("\nGenerating summary statistics...")
    generate_summary_statistics(df, output_dir)
    
    # Find top configurations
    print("Finding top configurations...")
    find_top_configurations(df, output_dir)
    
    # Generate plots
    print("\nGenerating plots...")
    plot_l1d_size_impact(df, output_dir)
    plot_l2_size_impact(df, output_dir)
    plot_associativity_impact(df, output_dir)
    plot_performance_heatmap(df, output_dir)
    plot_pareto_frontier(df, output_dir)
    
    # Generate single parameter analysis if requested
    if args.single_param:
        print(f"\nGenerating single parameter analysis for: {args.single_param}...")
        extract_single_parameter_analysis(df, output_dir, args.single_param)
    
    # Generate Part 3 interaction plots
    print("\nGenerating Part 3 interaction plots...")
    create_interaction_heatmaps(df, output_dir)
    
    # Generate design recommendations
    print("\nGenerating design recommendations...")
    generate_design_recommendations(df, output_dir)
    
    print("ANALYSIS COMPLETE!")
    print("="*70)
    print(f"\nAll outputs saved to: {output_dir}/")
    print("\nGenerated files:")
    print("  Tables:")
    print("    - full_results_table.csv")
    print("    - summary_statistics.csv")
    print("    - top3_execution_time.csv")
    print("    - top3_l1d_hit_rate.csv")
    print("    - top3_l2_hit_rate.csv")
    print("    - design_recommendations.csv")
    if args.single_param:
        print(f"    - single_param_{args.single_param}_table.csv")
    print("  Plots:")
    print("    - l1d_size_impact.png")
    print("    - l2_size_impact.png")
    print("    - associativity_impact.png")
    print("    - performance_heatmap.png")
    print("    - pareto_frontier.png")
    if args.single_param:
        print(f"    - single_param_{args.single_param}.png")
    print("  Part 3 Interaction Plots:")
    print("    - interaction_plots/interaction_l1d_l2_size.png")
    print("    - interaction_plots/interaction_l1d_l2_assoc.png")
    print("    - interaction_plots/interaction_l1d_size_assoc.png")
    print("    - interaction_plots/interaction_l2_size_assoc.png")
    print("    - interaction_plots/interaction_execution_time.png")

if __name__ == '__main__':
    main()
